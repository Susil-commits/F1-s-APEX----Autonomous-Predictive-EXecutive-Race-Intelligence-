"""APEX LLM Narration Service & Sporting Regulations RAG Layer.

Operates strictly on top of core/api/predict.py without altering core prediction
or sensitivity logic. Provides:
1. FIA Technical & Sporting Regulations file-based vector retrieval (RAG).
2. Fluent Formula 1 Race Engineer narrative briefing grounded strictly on computed metrics.
3. Zero-degradation fallback: LLM failures or timeouts return structured prediction without error.
"""
from __future__ import annotations

import glob
import logging
import os
import re
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Request
from pydantic import Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from core.api.limiter import limiter
from core.api.predict import (
    PredictRequest,
    PredictResponse,
    predict_finish,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/core", tags=["Narration & Strategy Intelligence"])

REGULATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "regulations")


class RegulationChunk:
    """Represents a chunked FIA Sporting/Technical Regulation unit."""

    def __init__(
        self,
        chunk_id: str,
        topic: str,
        article: str,
        levers: List[str],
        text: str,
    ):
        self.chunk_id = chunk_id
        self.topic = topic
        self.article = article
        self.levers = levers
        self.text = text


class RegulationsVectorStore:
    """Lightweight file-based vector retriever for F1 Technical & Sporting Regulations.

    Uses scikit-learn TF-IDF + Cosine Similarity over chunked markdown documents.
    Operates in-memory with sub-millisecond query latency and zero external dependencies.
    """

    def __init__(self, regulations_dir: str = REGULATIONS_DIR):
        self.regulations_dir = regulations_dir
        self.chunks: List[RegulationChunk] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix: Any = None
        self._load_and_index()

    def _load_and_index(self) -> None:
        """Parses regulatory markdown documents and builds TF-IDF vector index."""
        md_files = glob.glob(os.path.join(self.regulations_dir, "*.md"))
        self.chunks.clear()

        for file_path in md_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract title/article from header
                topic_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                topic = topic_match.group(1).strip() if topic_match else os.path.basename(file_path)

                article_match = re.search(r"Article\s+[0-9.]+(?:\([a-z0-9]+\))?", topic, re.IGNORECASE)
                article = article_match.group(0).strip() if article_match else "FIA Regulations"

                # Extract levers mentioned in doc
                levers = re.findall(r"`([a-zA-Z0-9_]+)`", content)

                # Split by sections or numbered clauses for granular chunking
                sections = re.split(r"\n(?=##\s+|\d+\.\s+\*\*)", content)
                for idx, sec in enumerate(sections):
                    cleaned = sec.strip()
                    if len(cleaned) < 40:
                        continue
                    clause_match = re.search(r"\*\*(Article\s+[0-9.]+(?:\([a-z0-9]+\))?[^*]*)\*\*", cleaned)
                    sec_article = clause_match.group(1) if clause_match else article
                    chunk = RegulationChunk(
                        chunk_id=f"{os.path.basename(file_path)}#{idx}",
                        topic=topic,
                        article=sec_article,
                        levers=levers,
                        text=cleaned,
                    )
                    self.chunks.append(chunk)
            except Exception as exc:
                logger.warning(f"[RegulationsVectorStore] Failed to parse {file_path}: {exc}")

        if self.chunks:
            # Build search corpus combining text and target lever tags
            corpus = [f"{c.topic} {' '.join(c.levers)} {c.text}" for c in self.chunks]
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, top_k: int = 1, threshold: float = 0.08) -> List[Dict[str, Any]]:
        """Retrieves most relevant regulation chunks for a given query or strategy lever."""
        if not self.chunks or self.vectorizer is None or self.tfidf_matrix is None:
            return []

        # Exact lever tag boost
        lever_matches = [
            c for c in self.chunks if any(l.lower() == query.strip().lower() for l in c.levers)
        ]

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        ranked_indices = similarities.argsort()[::-1]
        results: List[Dict[str, Any]] = []

        # If direct lever tag match exists, ensure it is ranked top
        if lever_matches:
            top_match = lever_matches[0]
            idx = self.chunks.index(top_match)
            sim_score = max(float(similarities[idx]), 0.85)
            results.append({
                "topic": top_match.topic,
                "article": top_match.article,
                "similarity": round(sim_score, 3),
                "excerpt": top_match.text[:280].strip() + ("..." if len(top_match.text) > 280 else ""),
            })

        for idx in ranked_indices:
            score = float(similarities[idx])
            chunk = self.chunks[idx]
            if score >= threshold and not any(r["topic"] == chunk.topic and r["article"] == chunk.article for r in results):
                results.append({
                    "topic": chunk.topic,
                    "article": chunk.article,
                    "similarity": round(score, 3),
                    "excerpt": chunk.text[:280].strip() + ("..." if len(chunk.text) > 280 else ""),
                })
            if len(results) >= top_k:
                break

        return results[:top_k]


_REGULATIONS_STORE: Optional[RegulationsVectorStore] = None


def get_regulations_store() -> RegulationsVectorStore:
    """Returns singleton RegulationsVectorStore instance."""
    global _REGULATIONS_STORE
    if _REGULATIONS_STORE is None:
        _REGULATIONS_STORE = RegulationsVectorStore()
    return _REGULATIONS_STORE


class NarratePredictResponse(PredictResponse):
    """Extended prediction response including race engineer narrative and audit sources."""

    narrative: Optional[str] = Field(
        None,
        description="Fluent race-engineer tactical debrief strictly grounded in computed numbers",
    )
    retrieved_sources: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Audited FIA sporting & technical regulation chunks grounding the briefing",
    )


def format_race_engineer_prompt(
    prediction: PredictResponse,
    retrieved_sources: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Builds strictly grounded prompt from already-computed structured prediction output."""
    levers_text = "None identified"
    if prediction.strategy_recommendations:
        levers_text = "\n".join([
            f"- Lever: {r.lever} by {r.change:+.2f}s | Gain: {r.positions_gained:+.1f} positions (P{r.predicted_position_before} -> P{r.predicted_position_after})"
            for r in prediction.strategy_recommendations
        ])

    opp_text = "None"
    if prediction.biggest_opportunity:
        bo = prediction.biggest_opportunity
        opp_text = f"{bo.label} (Value: {bo.value}, Importance: {bo.importance_pct}%, Opportunity Score: {bo.opportunity_score})"

    regs_text = "No regulation constraints applicable."
    if retrieved_sources:
        regs_text = "\n".join([
            f"- [{s['article']}] {s['topic']}: {s['excerpt']}"
            for s in retrieved_sources
        ])

    prompt = (
        f"Driver: {prediction.driver_name} ({prediction.driver_id})\n"
        f"Team: {prediction.team_name}\n"
        f"Circuit / Race ID: {prediction.race_id}\n"
        f"Grid Position: P{prediction.grid_position}\n"
        f"APEX Predicted Finish: P{prediction.predicted_position}\n"
        f"Confidence Window: P{prediction.confidence_interval[0]} to P{prediction.confidence_interval[1]}\n"
        f"Win Probability: {prediction.win_probability_pct}%\n"
        f"Podium Probability: {prediction.podium_probability_pct}%\n\n"
        f"Top Strategy Levers:\n{levers_text}\n\n"
        f"Biggest Optimization Opportunity:\n{opp_text}\n\n"
        f"Governing FIA Regulation Context:\n{regs_text}\n"
    )
    return prompt


async def generate_race_engineer_narrative(
    prediction: PredictResponse,
    retrieved_sources: Optional[List[Dict[str, Any]]] = None,
    timeout_seconds: float = 4.0,
) -> Optional[str]:
    """Generates race-engineer tactical narrative via LLM with strict numerical grounding.

    Fails gracefully returning None on any network error, timeout, or missing key.
    """
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if not groq_key and not openai_key and not gemini_key:
        logger.info("[Narration] No LLM API key configured (GROQ_API_KEY/OPENAI_API_KEY). Skipping narrative.")
        return None

    system_instruction = (
        "You are an elite Formula 1 Race Strategy Engineer briefing your driver over the team radio before the race. "
        "Your briefing must be fluent, authoritative, tactically decisive, and concise (2 to 3 sentences). "
        "CRITICAL GROUNDING RULES:\n"
        "1. Strictly use ONLY the numerical values, positions, and probabilities provided in the prompt.\n"
        "2. DO NOT invent lap times, deltas, tire compounds, or gap seconds not explicitly provided.\n"
        "3. If FIA regulation context is provided, reference the rule to justify why the tactical lever is constrained.\n"
        "4. Tone must be professional, focused, and realistic."
    )

    user_prompt = format_race_engineer_prompt(prediction, retrieved_sources)

    # Determine endpoint, model, and headers
    if groq_key:
        api_url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
        model = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
        if "/" in model:
            # Normalize e.g. groq/compound-mini to a valid Groq model
            model = "llama-3.1-8b-instant"
    elif openai_key:
        api_url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    else:
        api_url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        headers = {"Authorization": f"Bearer {gemini_key}", "Content-Type": "application/json"}
        model = "gemini-2.0-flash"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 200,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.post(api_url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                return content
            else:
                logger.warning(
                    f"[Narration LLM HTTP {resp.status_code}] Failed generating narrative: {resp.text[:200]}"
                )
                return None
    except Exception as exc:
        logger.warning(f"[Narration LLM Exception] Gracefully degrading: {exc}")
        return None


@router.post(
    "/predict/narrate",
    response_model=NarratePredictResponse,
    response_model_exclude_none=True,
)
@limiter.limit("30/minute")
async def predict_with_narration(request: Request, req: PredictRequest):
    """Tier 1 Prediction with LLM Race Engineer Strategy Narration & Audited Regulations RAG.

    1. Executes unchanged core prediction + sensitivity logic.
    2. Retrieves governing FIA technical/sporting regulations for identified levers.
    3. Synthesizes a fluent, numerically-grounded briefing.
    4. Falls back cleanly without error if LLM is unavailable.
    """
    # Step 1: Call existing prediction logic unchanged
    prediction: PredictResponse = await predict_finish(request, req)

    # Step 2: Retrieve regulation grounding for active levers (Component 2 & 3)
    reg_store = get_regulations_store()
    retrieved_sources: List[Dict[str, Any]] = []

    query_candidates: List[str] = []
    for lever in prediction.strategy_recommendations:
        query_candidates.append(lever.lever)

    if prediction.biggest_opportunity:
        query_candidates.append(prediction.biggest_opportunity.feature)

    if req.weather_transition or (req.rain_probability and req.rain_probability > 0.3):
        query_candidates.append("weather_transition_flag")

    for candidate in query_candidates[:2]:
        matched = reg_store.retrieve(candidate, top_k=1)
        for m in matched:
            if not any(s["topic"] == m["topic"] for s in retrieved_sources):
                retrieved_sources.append(m)

    # Step 3: LLM narration synthesis (Component 1)
    narrative = await generate_race_engineer_narrative(
        prediction=prediction,
        retrieved_sources=retrieved_sources if retrieved_sources else None,
    )

    # Step 4: Construct NarratePredictResponse
    pred_dict = prediction.model_dump()
    pred_dict["narrative"] = narrative
    pred_dict["retrieved_sources"] = retrieved_sources if retrieved_sources else None

    return NarratePredictResponse(**pred_dict)
