"""Unit & integration tests for HybridMissionRAG (FAISS + BM25 + LangChain)."""
import os
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pytest

from backend.app.intelligence.hybrid_mission_rag import (
    ApexHybridRAGRetriever,
    HybridMissionRAG,
    tokenize_for_bm25,
)
from backend.app.simulator.models import DecisionExplanation, StrategyAction


@pytest.fixture
def temp_rag_engine():
    """Creates an isolated HybridMissionRAG engine in a temporary directory."""
    temp_dir = tempfile.mkdtemp()
    idx_path = Path(temp_dir) / "test_faiss.index"
    meta_path = Path(temp_dir) / "test_meta.json"

    rag = HybridMissionRAG(
        dimension=384,
        index_path=idx_path,
        meta_path=meta_path,
        rrf_k=60,
    )

    sample_logs = [
        {
            "race_id": "test_silverstone",
            "lap": 12,
            "recommendation": "MAINTAIN",
            "confidence_score": 0.85,
            "urgency": "LOW",
            "rule_action": "MAINTAIN",
            "dqn_action": "MAINTAIN",
            "tyre_cliff_risk": "LOW",
            "explanation_payload": {
                "primary_factors": ["Tyre wear stable at 25%", "Clear air gap +3.2s"],
                "commentary": "Maintain current stint pacing.",
            },
        },
        {
            "race_id": "test_silverstone",
            "lap": 24,
            "recommendation": "PIT_HARD",
            "confidence_score": 0.96,
            "urgency": "CRITICAL",
            "rule_action": "PIT_HARD",
            "dqn_action": "PIT_HARD",
            "tyre_cliff_risk": "HIGH",
            "explanation_payload": {
                "primary_factors": ["Safety Car deployed", "Tyre wear 68% approaching cliff"],
                "commentary": "Box now for Hard tyres under Safety Car neutralization.",
            },
        },
        {
            "race_id": "test_silverstone",
            "lap": 36,
            "recommendation": "PUSH",
            "confidence_score": 0.91,
            "urgency": "HIGH",
            "rule_action": "PUSH",
            "dqn_action": "PUSH",
            "tyre_cliff_risk": "LOW",
            "explanation_payload": {
                "primary_factors": ["Undercut success", "Target car within DRS detection zone 0.7s"],
                "commentary": "Deploy maximum battery power to overtake.",
            },
        },
    ]

    rag.sync_index(sample_logs, persist=True)

    yield rag, sample_logs

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_bm25_tokenization():
    """Verify regex tokenization for sparse indexing."""
    tokens = tokenize_for_bm25("Lap 24: Strategy Directive: PIT_HARD (Safety Car).")
    assert "lap" in tokens
    assert "24" in tokens
    assert "pit_hard" in tokens or "pit" in tokens
    assert "safety" in tokens


def test_faiss_dense_search(temp_rag_engine):
    """Verify that FAISS dense index returns relevant candidate logs."""
    rag, _ = temp_rag_engine

    results = rag.search(query="safety car pit stop opportunity", top_k=2)
    assert len(results) > 0
    top_doc, score = results[0]
    assert top_doc["lap"] == 24
    assert "PIT_HARD" in top_doc["recommendation"]
    assert score > 0.0


def test_hybrid_rrf_scoring_with_lap_boost(temp_rag_engine):
    """Verify that Reciprocal Rank Fusion correctly applies lap-specific boost."""
    rag, _ = temp_rag_engine

    # Query specifically targeting lap 36 push phase
    results = rag.search(query="What was our directive on lap 36?", top_k=1, target_lap=36)
    assert len(results) == 1
    top_doc, score = results[0]
    assert top_doc["lap"] == 36
    assert top_doc["recommendation"] == "PUSH"
    # RRF score should have the +1.5 lap boost
    assert score >= 1.5


def test_faiss_disk_persistence(temp_rag_engine):
    """Verify FAISS binary and metadata are saved and reloaded from disk without data loss."""
    rag, sample_logs = temp_rag_engine

    assert rag.index_path.exists()
    assert rag.meta_path.exists()

    # Create a fresh engine pointing to the same disk files
    fresh_rag = HybridMissionRAG(
        dimension=384,
        index_path=rag.index_path,
        meta_path=rag.meta_path,
    )

    assert len(fresh_rag.documents) == len(sample_logs)
    results = fresh_rag.search(query="safety car box", top_k=1)
    assert len(results) == 1
    assert results[0][0]["lap"] == 24


def test_langchain_base_retriever_interface(temp_rag_engine):
    """Verify LangChain BaseRetriever compliance and Document metadata formatting."""
    rag, _ = temp_rag_engine

    retriever = ApexHybridRAGRetriever(rag_engine=rag, top_k=2)
    docs = retriever.invoke("safety car tyre degradation") if hasattr(retriever, "invoke") else retriever.get_relevant_documents("safety car tyre degradation")

    assert len(docs) > 0
    top_doc = docs[0]
    assert hasattr(top_doc, "page_content")
    assert hasattr(top_doc, "metadata")
    assert top_doc.metadata["lap"] in (12, 24, 36)
    assert "rrf_score" in top_doc.metadata

    # Also test backward-compatible helper
    docs_legacy = retriever.get_relevant_documents("safety car tyre degradation")
    assert len(docs_legacy) > 0
