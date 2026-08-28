"""Hybrid Mission RAG (Retrieval-Augmented Generation) Engine for APEX.

Combines FAISS dense vector search (faiss.IndexFlatIP) with BM25 sparse keyword ranking
via Reciprocal Rank Fusion (RRF), with disk index persistence and LangChain BaseRetriever compliance.
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, List, Optional, Tuple

import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None  # type: ignore
    FAISS_AVAILABLE = False

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25Okapi = None  # type: ignore
    BM25_AVAILABLE = False

try:
    from langchain_core.documents import Document
    from langchain_core.retrievers import BaseRetriever
    from pydantic import ConfigDict, Field
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain.schema import Document
        from langchain.schema.retriever import BaseRetriever
        from pydantic import ConfigDict, Field
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False
        Document = Any  # type: ignore
        BaseRetriever = object  # type: ignore
        Field = lambda **kwargs: None  # type: ignore
        ConfigDict = dict  # type: ignore

from backend.app.intelligence.embeddings import (
    embed_text,
    embed_texts,
    format_decision_log,
)

logger = logging.getLogger(__name__)

DEFAULT_INDEX_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DEFAULT_INDEX_PATH = DEFAULT_INDEX_DIR / "faiss_rag.index"
DEFAULT_META_PATH = DEFAULT_INDEX_DIR / "faiss_rag_metadata.json"


def tokenize_for_bm25(text: str) -> list[str]:
    """Tokenizes text for BM25 sparse index."""
    return re.findall(r"\w+", text.lower())


class HybridMissionRAG:
    """Industrial-grade Hybrid RAG fusing FAISS dense inner-product indexing with BM25 sparse search."""

    _instance: Optional["HybridMissionRAG"] = None

    def __init__(
        self,
        dimension: int = 384,
        index_path: Optional[str | Path] = None,
        meta_path: Optional[str | Path] = None,
        rrf_k: int = 60,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4,
    ):
        self.dimension = dimension
        self.index_path = Path(index_path or DEFAULT_INDEX_PATH)
        self.meta_path = Path(meta_path or DEFAULT_META_PATH)
        self.rrf_k = rrf_k
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight

        self.documents: list[dict[str, Any]] = []
        self.doc_texts: list[str] = []
        self.doc_tokens: list[list[str]] = []
        self.bm25: Any = None
        self.faiss_index: Any = None

        self._init_dense_index()
        self._load_from_disk_if_exists()

    def _init_dense_index(self):
        """Initializes FAISS IndexFlatIP (cosine similarity over normalized embeddings)."""
        if FAISS_AVAILABLE and faiss is not None:
            self.faiss_index = faiss.IndexFlatIP(self.dimension)
            logger.info(f"[HybridMissionRAG] Initialized FAISS IndexFlatIP (dim={self.dimension}).")
        else:
            logger.warning("[HybridMissionRAG] FAISS not available. Using dense numpy fallback.")
            self.faiss_index = None

    @classmethod
    def get_instance(cls) -> "HybridMissionRAG":
        """Singleton accessor for APEX Hybrid RAG Engine."""
        if cls._instance is None:
            cls._instance = HybridMissionRAG()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Resets singleton instance for test teardown."""
        cls._instance = None

    def _load_from_disk_if_exists(self) -> bool:
        """Loads FAISS index and metadata from disk if available."""
        if not self.index_path.exists() or not self.meta_path.exists():
            return False

        try:
            if FAISS_AVAILABLE and faiss is not None:
                self.faiss_index = faiss.read_index(str(self.index_path))
            
            with open(self.meta_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                self.documents = saved_data.get("documents", [])
                self.doc_texts = saved_data.get("doc_texts", [])

            self.doc_tokens = [tokenize_for_bm25(t) for t in self.doc_texts]
            if BM25_AVAILABLE and BM25Okapi is not None and self.doc_tokens:
                self.bm25 = BM25Okapi(self.doc_tokens)

            logger.info(f"[HybridMissionRAG] Successfully loaded FAISS index and {len(self.documents)} records from disk.")
            return True
        except Exception as e:
            logger.warning(f"[HybridMissionRAG] Could not load index from disk ({e}). Initializing empty.")
            self._init_dense_index()
            self.documents = []
            self.doc_texts = []
            self.doc_tokens = []
            self.bm25 = None
            return False

    def persist_to_disk(self) -> bool:
        """Persists the FAISS index binary and metadata documents to disk."""
        try:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            self.meta_path.parent.mkdir(parents=True, exist_ok=True)

            if FAISS_AVAILABLE and faiss is not None and self.faiss_index is not None:
                faiss.write_index(self.faiss_index, str(self.index_path))

            with open(self.meta_path, "w", encoding="utf-8") as f:
                json.dump({
                    "version": "1.0",
                    "documents": self.documents,
                    "doc_texts": self.doc_texts,
                }, f, indent=2)

            logger.info(f"[HybridMissionRAG] Saved {len(self.documents)} records to FAISS index on disk ({self.index_path}).")
            return True
        except Exception as e:
            logger.error(f"[HybridMissionRAG] Error persisting FAISS index: {e}")
            return False

    def sync_index(self, logs: list[dict[str, Any]], persist: bool = True) -> int:
        """
        Rebuilds the FAISS dense index and BM25 sparse index over the provided decision logs.
        """
        if not logs:
            self._init_dense_index()
            self.documents = []
            self.doc_texts = []
            self.doc_tokens = []
            self.bm25 = None
            return 0

        self.documents = list(logs)
        self.doc_texts = [format_decision_log(item) for item in self.documents]
        self.doc_tokens = [tokenize_for_bm25(t) for t in self.doc_texts]

        # 1. Build Dense FAISS Index
        embeddings = embed_texts(self.doc_texts)  # [N, dim], normalized float32
        if embeddings.shape[1] != self.dimension:
            # Adjust dimension dynamically if embedding model dimension differs
            self.dimension = embeddings.shape[1]

        if FAISS_AVAILABLE and faiss is not None:
            self.faiss_index = faiss.IndexFlatIP(self.dimension)
            emb_f32 = np.ascontiguousarray(embeddings, dtype=np.float32)
            self.faiss_index.add(emb_f32)
        else:
            self._dense_embeddings_fallback = embeddings

        # 2. Build Sparse BM25 Index
        if BM25_AVAILABLE and BM25Okapi is not None and self.doc_tokens:
            self.bm25 = BM25Okapi(self.doc_tokens)
        else:
            self.bm25 = None

        if persist:
            self.persist_to_disk()

        logger.info(f"[HybridMissionRAG] Synchronized hybrid index with {len(self.documents)} records.")
        return len(self.documents)

    def search(
        self,
        query: str,
        race_id: Optional[str] = None,
        top_k: int = 5,
        target_lap: Optional[int] = None,
    ) -> list[tuple[dict[str, Any], float]]:
        """
        Executes hybrid dense-sparse search fused via Reciprocal Rank Fusion (RRF).
        Returns list of (decision_log, rrf_score) sorted descending by relevance.
        """
        if not self.documents:
            return []

        # Filter candidate indices by race_id if specified
        valid_indices = [
            i for i, d in enumerate(self.documents)
            if race_id is None or d.get("race_id") == race_id
        ]
        if not valid_indices:
            return []

        num_candidates = len(valid_indices)
        k_search = min(len(self.documents), max(top_k * 3, 20))

        # --- 1. Dense Vector Search (FAISS) ---
        q_emb = embed_text(query)  # [dim]
        dense_rankings: dict[int, int] = {}  # doc_idx -> rank (1-indexed)

        if FAISS_AVAILABLE and faiss is not None and self.faiss_index is not None and self.faiss_index.ntotal > 0:
            q_emb_f32 = np.ascontiguousarray(q_emb.reshape(1, -1), dtype=np.float32)
            distances, indices = self.faiss_index.search(q_emb_f32, k_search)
            rank = 1
            for idx in indices[0]:
                if idx != -1 and idx in valid_indices:
                    dense_rankings[idx] = rank
                    rank += 1
        else:
            # Dense fallback using numpy cosine similarities
            all_embs = getattr(self, "_dense_embeddings_fallback", embed_texts(self.doc_texts))
            sims = np.dot(all_embs, q_emb)
            sorted_dense = np.argsort(-sims)
            rank = 1
            for idx in sorted_dense:
                if idx in valid_indices:
                    dense_rankings[idx] = rank
                    rank += 1
                    if rank > k_search:
                        break

        # --- 2. Sparse Search (BM25) ---
        sparse_rankings: dict[int, int] = {}  # doc_idx -> rank (1-indexed)
        q_tokens = tokenize_for_bm25(query)

        if self.bm25 is not None and q_tokens:
            bm25_scores = self.bm25.get_scores(q_tokens)
            sorted_sparse = np.argsort(-np.array(bm25_scores))
            rank = 1
            for idx in sorted_sparse:
                if idx in valid_indices and bm25_scores[idx] > 0.0:
                    sparse_rankings[idx] = rank
                    rank += 1
                    if rank > k_search:
                        break
        else:
            # Token overlap fallback
            q_set = set(q_tokens)
            overlap_scores = [
                len(q_set.intersection(set(self.doc_tokens[i]))) if i < len(self.doc_tokens) else 0
                for i in range(len(self.documents))
            ]
            sorted_sparse = np.argsort(-np.array(overlap_scores))
            rank = 1
            for idx in sorted_sparse:
                if idx in valid_indices and overlap_scores[idx] > 0:
                    sparse_rankings[idx] = rank
                    rank += 1
                    if rank > k_search:
                        break

        # --- 3. Reciprocal Rank Fusion (RRF) ---
        all_candidate_indices = set(dense_rankings.keys()).union(set(sparse_rankings.keys()))
        if not all_candidate_indices:
            all_candidate_indices = set(valid_indices[:k_search])

        rrf_scores: dict[int, float] = {}
        for idx in all_candidate_indices:
            score = 0.0
            if idx in dense_rankings:
                score += self.dense_weight / (self.rrf_k + dense_rankings[idx])
            if idx in sparse_rankings:
                score += self.sparse_weight / (self.rrf_k + sparse_rankings[idx])
            
            # Boost score if exact lap requested matches
            if target_lap is not None and self.documents[idx].get("lap") == target_lap:
                score += 1.5

            rrf_scores[idx] = score

        # Sort candidate documents by RRF score descending
        sorted_candidates = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)
        results = [
            (self.documents[idx], round(score, 5))
            for idx, score in sorted_candidates[:top_k]
        ]
        return results


# Module singleton
hybrid_rag_engine = HybridMissionRAG.get_instance()


# ---------------------------------------------------------------------------
# Phase 3 — LangChain BaseRetriever Wrapper
# ---------------------------------------------------------------------------

if LANGCHAIN_AVAILABLE:
    class ApexHybridRAGRetriever(BaseRetriever):
        """LangChain BaseRetriever wrapper for APEX FAISS+BM25 Hybrid RAG."""

        rag_engine: HybridMissionRAG = Field(default_factory=HybridMissionRAG.get_instance)
        race_id: Optional[str] = None
        top_k: int = 5

        model_config = ConfigDict(arbitrary_types_allowed=True)

        def _get_relevant_documents(
            self,
            query: str,
            *,
            run_manager: Any = None,
        ) -> list[Document]:
            """Synchronous LangChain document retrieval."""
            lap_match = re.search(r"\blap\s*(\d+)\b", query.lower())
            target_lap = int(lap_match.group(1)) if lap_match else None

            results = self.rag_engine.search(
                query=query,
                race_id=self.race_id,
                top_k=self.top_k,
                target_lap=target_lap,
            )

            docs = []
            for doc_dict, score in results:
                content = format_decision_log(doc_dict)
                metadata = {
                    "race_id": doc_dict.get("race_id"),
                    "lap": doc_dict.get("lap"),
                    "recommendation": doc_dict.get("recommendation"),
                    "confidence_score": doc_dict.get("confidence_score"),
                    "urgency": doc_dict.get("urgency"),
                    "rule_action": doc_dict.get("rule_action"),
                    "dqn_action": doc_dict.get("dqn_action"),
                    "tyre_cliff_risk": doc_dict.get("tyre_cliff_risk"),
                    "rrf_score": score,
                }
                docs.append(Document(page_content=content, metadata=metadata))
            return docs

        def get_relevant_documents(self, query: str) -> list[Document]:
            """Backward-compatible helper for legacy LangChain retriever callers."""
            return self._get_relevant_documents(query=query)

        async def _aget_relevant_documents(
            self,
            query: str,
            *,
            run_manager: Any = None,
        ) -> list[Document]:
            """Asynchronous LangChain document retrieval."""
            return self._get_relevant_documents(query=query, run_manager=run_manager)
else:
    class ApexHybridRAGRetriever:  # type: ignore
        """Fallback when LangChain is not installed."""
        def __init__(self, *args, **kwargs):
            pass

        def get_relevant_documents(self, query: str) -> list[Any]:
            return []
