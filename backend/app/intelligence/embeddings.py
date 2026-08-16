"""Dense Vector Embeddings Layer for APEX Race History RAG.

Utilizes local sentence-transformers (all-MiniLM-L6-v2) for semantic retrieval over
persisted DecisionLogModel telemetry events and race strategy provenance trails.
"""
from typing import List, Dict, Any, Optional, Union
import os
import logging
import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"


class DecisionEmbedder:
    """Manages dense vector encoding of telemetry decision logs and natural language queries."""

    _instance: Optional["DecisionEmbedder"] = None

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        self.model_name = model_name
        self.model: Any = None
        self._is_transformer_active = False
        self._init_encoder()

    def _init_encoder(self):
        """Initializes SentenceTransformer encoder with local cache and fallback resilience."""
        try:
            from sentence_transformers import SentenceTransformer
            # Load model locally
            self.model = SentenceTransformer(self.model_name)
            self._is_transformer_active = True
            logger.info(f"[DecisionEmbedder] Loaded SentenceTransformer '{self.model_name}' successfully.")
        except Exception as e:
            logger.warning(f"[DecisionEmbedder] SentenceTransformer initialization note ({e}). Using deterministic embedding fallback.")
            self._is_transformer_active = False
            self.model = None

    @classmethod
    def get_instance(cls) -> "DecisionEmbedder":
        if cls._instance is None:
            cls._instance = DecisionEmbedder()
        return cls._instance

    @staticmethod
    def format_log_as_text(entry: Dict[str, Any]) -> str:
        """Serializes a DecisionLogModel / stored decision record into rich semantic text."""
        lap = entry.get("lap", 1)
        rec = entry.get("recommendation", "MAINTAIN")
        conf = entry.get("confidence_score", 0.85)
        conf_pct = int(conf * 100) if conf <= 1.0 else int(conf)
        urgency = entry.get("urgency", "MEDIUM")
        rule_act = entry.get("rule_action", "MAINTAIN")
        dqn_act = entry.get("dqn_action", "MAINTAIN")
        cliff_risk = entry.get("tyre_cliff_risk", "LOW")
        race_id = entry.get("race_id", "")

        expl = entry.get("explanation_payload") or entry.get("decision") or {}
        factors = expl.get("primary_factors", [])
        factors_str = "; ".join(factors) if factors else "Standard race stint management"
        commentary = expl.get("commentary", "")
        pit_status = expl.get("pit_window_status", "OPTIMAL")

        parts = [
            f"Race {race_id} Lap {lap}:",
            f"Strategy Directive: {rec} (Urgency: {urgency}, Confidence: {conf_pct}%).",
            f"Drivers & Attributions: {factors_str}.",
            f"Consensus: Rule engine recommended {rule_act}, DQN RL agent selected {dqn_act}.",
            f"Tyre Cliff Risk: {cliff_risk}. Pit Window: {pit_status}.",
        ]
        if commentary:
            parts.append(f"Team Radio: '{commentary}'.")

        return " ".join(parts)

    def embed_text(self, text: str) -> np.ndarray:
        """Encodes a single text string into a normalized 1D float32 numpy vector."""
        if self._is_transformer_active and self.model is not None:
            try:
                emb = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
                return np.asarray(emb, dtype=np.float32)
            except Exception as e:
                logger.debug(f"[DecisionEmbedder] Transformer encode error: {e}")

        # Deterministic hashing vectorizer fallback (384-dimensional)
        return self._deterministic_fallback_vector(text)

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Encodes a list of text strings into a 2D float32 numpy matrix [N, dim]."""
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        if self._is_transformer_active and self.model is not None:
            try:
                embs = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
                return np.asarray(embs, dtype=np.float32)
            except Exception as e:
                logger.debug(f"[DecisionEmbedder] Transformer batch encode error: {e}")

        # Batch fallback
        vectors = [self._deterministic_fallback_vector(t) for t in texts]
        return np.vstack(vectors)

    def embed_decision_log(self, entry: Dict[str, Any]) -> np.ndarray:
        """Formats and embeds a single decision log entry."""
        text = self.format_log_as_text(entry)
        return self.embed_text(text)

    @property
    def embedding_source(self) -> str:
        """Returns 'sentence_transformer' if active, else 'hash_fallback'."""
        if self._is_transformer_active and self.model is not None:
            return "sentence_transformer"
        return "hash_fallback"

    def get_embedding_source(self) -> str:
        return self.embedding_source

    @staticmethod
    def _deterministic_fallback_vector(text: str, dim: int = 384) -> np.ndarray:
        """Deterministic, term-overlap pseudo-embedding when transformer weights are loading."""
        vec = np.zeros(dim, dtype=np.float32)
        words = text.lower().split()
        for i, w in enumerate(words):
            h = hash(w) % dim
            vec[h] += 1.0 / (1.0 + np.sqrt(i + 1))
        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec /= norm
        return vec


# Module-level convenience functions
embedder = DecisionEmbedder.get_instance()


def embed_text(text: str) -> np.ndarray:
    return embedder.embed_text(text)


def embed_texts(texts: List[str]) -> np.ndarray:
    return embedder.embed_texts(texts)


def embed_decision_log(entry: Dict[str, Any]) -> np.ndarray:
    return embedder.embed_decision_log(entry)


def format_decision_log(entry: Dict[str, Any]) -> str:
    return DecisionEmbedder.format_log_as_text(entry)


def get_embedding_source() -> str:
    return embedder.get_embedding_source()

