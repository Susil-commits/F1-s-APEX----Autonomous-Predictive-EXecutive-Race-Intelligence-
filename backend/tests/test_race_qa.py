"""Unit tests for APEX Race History RAG, embeddings, and grounding."""
import pytest
import numpy as np

from backend.app.twin.store import store
from backend.app.simulator.models import DecisionExplanation, StrategyAction
from backend.app.intelligence.embeddings import (
    embed_text,
    embed_texts,
    embed_decision_log,
    format_decision_log,
)
from backend.app.intelligence.race_qa import (
    RaceQAEngine,
    answer_race_question,
)


@pytest.fixture(autouse=True)
async def seed_decision_history():
    """Seeds test decision logs into store."""
    test_race_id = "test_rag_race_42"
    store.decision_history[test_race_id] = []

    # Lap 10: Maintain
    expl_10 = DecisionExplanation(
        recommendation=StrategyAction.MAINTAIN,
        confidence_score=0.88,
        urgency="LOW",
        primary_factors=["Stable medium tyre wear at 22%", "Good pace in clean air"],
        rule_engine_action=StrategyAction.MAINTAIN,
        dqn_action=StrategyAction.MAINTAIN,
        tyre_cliff_risk="LOW",
    )
    await store.log_decision(test_race_id, 10, expl_10)

    # Lap 23: Box for Hards due to safety car
    expl_23 = DecisionExplanation(
        recommendation=StrategyAction.PIT_HARD,
        confidence_score=0.96,
        urgency="CRITICAL",
        primary_factors=["Physical Safety Car deployed (12.0s cheap pit advantage)", "Tyre wear 65%"],
        rule_engine_action=StrategyAction.PIT_HARD,
        dqn_action=StrategyAction.PIT_HARD,
        tyre_cliff_risk="HIGH",
    )
    await store.log_decision(test_race_id, 23, expl_23)

    # Lap 35: Push mode
    expl_35 = DecisionExplanation(
        recommendation=StrategyAction.PUSH,
        confidence_score=0.92,
        urgency="HIGH",
        primary_factors=["Fresh hard tyres", "Attacking car ahead within DRS gap 0.8s"],
        rule_engine_action=StrategyAction.PUSH,
        dqn_action=StrategyAction.PUSH,
        tyre_cliff_risk="LOW",
    )
    await store.log_decision(test_race_id, 35, expl_35)

    return test_race_id


def test_embeddings_generation():
    """Verifies that dense embeddings return valid normalized vectors."""
    vec = embed_text("Lap 23 pit stop under Safety Car")
    assert isinstance(vec, np.ndarray)
    assert vec.ndim == 1
    assert len(vec) in [384, 768]
    assert np.isclose(np.linalg.norm(vec), 1.0, atol=1e-3)

    batch_vecs = embed_texts(["Lap 1", "Lap 2", "Lap 3"])
    assert batch_vecs.shape[0] == 3


@pytest.mark.asyncio
async def test_retrieve_relevant_decisions(seed_decision_history):
    """Verifies that retrieval correctly identifies the relevant historical lap."""
    qa = RaceQAEngine()
    
    # Query specifically about lap 23 / safety car
    results = await qa.retrieve_relevant_decisions(
        query="Why did we pit on lap 23?",
        race_id=seed_decision_history,
        top_k=2,
    )
    assert len(results) > 0
    top_decision, score = results[0]
    assert top_decision["lap"] == 23
    assert "PIT_HARD" in str(top_decision["recommendation"])


@pytest.mark.asyncio
async def test_answer_race_question_factual(seed_decision_history):
    """Verifies that answer_race_question provides grounded answer and citations."""
    response = await answer_race_question(
        query="What was our directive on lap 23?",
        race_id=seed_decision_history,
    )
    assert "answer" in response
    assert len(response["sources"]) > 0
    assert response["sources"][0]["lap"] == 23
    assert "PIT_HARD" in response["sources"][0]["recommendation"]
    assert "embedding_source" in response
    assert response["embedding_source"] in ["sentence_transformer", "hash_fallback"]


@pytest.mark.asyncio
async def test_answer_race_question_unanswerable_lap(seed_decision_history):
    """Verifies that querying a non-existent lap explicitly refrains from hallucinating."""
    response = await answer_race_question(
        query="What happened on lap 99?",
        race_id=seed_decision_history,
    )
    assert "embedding_source" in response
    assert response["embedding_source"] in ["sentence_transformer", "hash_fallback"]
    answer = response["answer"].lower()
    assert (
        "don't have that information" in answer
        or "no decision log exists" in answer
        or "lap 99" in answer
    )

