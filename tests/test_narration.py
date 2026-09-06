"""Tests for APEX Narration Service & Sporting Regulations RAG Layer.

Validates:
1. Narration happy path: returns structured predictions + fluent race engineer narrative.
2. Graceful degradation: LLM failure, timeout, or missing key falls back to structured data with no narrative field, never raising an error.
3. Regulations RAG retrieval: retrieved regulatory articles match the queried strategy levers (DRS for sectors, Parc Fermé for qualifying, Wet rules for rain/weather).
4. Predict endpoint independence: /api/core/predict continues to operate identically and independently.
"""
from unittest.mock import AsyncMock, patch
import pytest
from httpx import ASGITransport, AsyncClient

from core.api.main import app
from core.api.narration import get_regulations_store


@pytest.mark.asyncio
async def test_narration_endpoint_happy_path_mocked_llm():
    """Verifies narration endpoint returns structured predictions, narrative, and audited regulation sources."""
    transport = ASGITransport(app=app)
    mock_briefing = (
        "Box confirmation for Lando: APEX projects a P2 finish from P2 on the grid. "
        "Your highest leverage is Sector 2 where closing 0.2s gains +0.1 positions."
    )

    with patch("core.api.narration.generate_race_engineer_narrative", new=AsyncMock(return_value=mock_briefing)):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/api/core/predict/narrate",
                json={
                    "race_id": "silverstone",
                    "driver_id": "NOR",
                    "grid_position": 2,
                    "sector_2_delta_s": 0.2,
                },
            )
            assert res.status_code == 200
            data = res.json()

            # Structured prediction fields must remain intact
            assert data["driver_id"] == "NOR"
            assert data["team_name"] == "McLaren"
            assert 1 <= data["predicted_position"] <= 20
            assert "confidence_interval" in data
            assert len(data["confidence_interval"]) == 2
            assert "strategy_recommendations" in data

            # Narration field present
            assert "narrative" in data
            assert data["narrative"] == mock_briefing

            # Retrieved sources present and auditable
            assert "retrieved_sources" in data
            assert isinstance(data["retrieved_sources"], list)


@pytest.mark.asyncio
async def test_narration_endpoint_graceful_fallback_on_llm_failure():
    """Verifies that when LLM call fails, endpoint falls back gracefully with structured data and no narrative field."""
    transport = ASGITransport(app=app)

    # Simulate network timeout or LLM exception
    with patch("core.api.narration.generate_race_engineer_narrative", new=AsyncMock(return_value=None)):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/api/core/predict/narrate",
                json={
                    "race_id": "monza",
                    "driver_id": "VER",
                    "grid_position": 1,
                },
            )
            assert res.status_code == 200
            data = res.json()

            # Structured prediction fields must be fully populated
            assert data["driver_id"] == "VER"
            assert data["team_name"] == "Red Bull Racing"
            assert 1 <= data["predicted_position"] <= 20
            assert "win_probability_pct" in data
            assert "strategy_recommendations" in data

            # Narrative field must NOT be present when None (clean graceful fallback)
            assert "narrative" not in data, "Expected 'narrative' to be omitted on LLM failure"


@pytest.mark.asyncio
async def test_narration_llm_exception_handling_in_function():
    """Verifies generate_race_engineer_narrative handles internal exceptions gracefully."""
    from core.api.narration import generate_race_engineer_narrative
    from core.api.predict import PredictResponse

    mock_prediction = PredictResponse(
        race_id="silverstone",
        driver_id="HAM",
        driver_name="Lewis Hamilton",
        team_name="Ferrari",
        grid_position=5,
        predicted_position=4,
        confidence_interval=[2, 6],
        win_probability_pct=15.0,
        podium_probability_pct=60.0,
        model_version="core-v1.0.0",
        data_snapshot_utc="2026-09-07T00:00:00Z",
        feature_contributions=[],
        strategy_recommendations=[],
        biggest_opportunity=None,
        summary_explanation="Test summary",
    )

    # Force httpx.AsyncClient to raise a connection error
    with patch("httpx.AsyncClient.post", side_effect=Exception("Connection refused / Rate limited")):
        with patch.dict("os.environ", {"GROQ_API_KEY": "dummy_key"}):
            result = await generate_race_engineer_narrative(mock_prediction)
            assert result is None, "Expected None on exception without raising"


def test_regulations_rag_retrieval_matching():
    """Verifies that retrieved regulation content accurately matches the strategy lever it's attached to."""
    reg_store = get_regulations_store()

    # 1. Sector pace deltas -> must retrieve DRS regulations
    drs_results = reg_store.retrieve("sector_3_delta_s", top_k=1)
    assert len(drs_results) == 1
    assert "DRS" in drs_results[0]["topic"] or "Drag Reduction System" in drs_results[0]["topic"]
    assert "Article 21" in drs_results[0]["article"] or "Article 3.10" in drs_results[0]["article"]
    assert drs_results[0]["similarity"] > 0.3

    # 2. Qualifying delta to pole / grid position -> must retrieve Parc Fermé regulations
    parc_ferme_results = reg_store.retrieve("quali_delta_to_pole_s", top_k=1)
    assert len(parc_ferme_results) == 1
    assert "Parc Fermé" in parc_ferme_results[0]["topic"] or "Parc Ferme" in parc_ferme_results[0]["topic"]
    assert "Article 40" in parc_ferme_results[0]["article"] or "Sporting Regulations" in parc_ferme_results[0]["article"]
    assert parc_ferme_results[0]["similarity"] > 0.3

    # 3. Weather transition / rain probability -> must retrieve Tyre & Weather regulations
    tyre_results = reg_store.retrieve("weather_transition_flag", top_k=1)
    assert len(tyre_results) == 1
    assert "Tyre" in tyre_results[0]["topic"] or "Weather" in tyre_results[0]["topic"]
    assert "Article 30" in tyre_results[0]["article"] or "Wet" in tyre_results[0]["topic"]
    assert tyre_results[0]["similarity"] > 0.3


@pytest.mark.asyncio
async def test_existing_core_predict_unmodified_and_independent():
    """Verifies existing /api/core/predict endpoint continues working identically and independently."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/core/predict",
            json={
                "race_id": "monza",
                "driver_id": "NOR",
                "grid_position": 2,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["driver_id"] == "NOR"
        assert "predicted_position" in data
        assert "strategy_recommendations" in data
        assert "biggest_opportunity" in data
        # Ensure /api/core/predict does NOT have narrative or retrieved_sources
        assert "narrative" not in data
        assert "retrieved_sources" not in data
