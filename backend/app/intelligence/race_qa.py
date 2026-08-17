"""RAG (Retrieval-Augmented Generation) Engine over APEX Race Decision History.

Answers natural-language tactical queries grounded strictly in persisted DecisionLogModel
database records using dense vector retrieval (NumPy cosine similarity) and local Ollama LLMs.
"""
import logging
import re
from typing import Any

import numpy as np

from backend.app.intelligence.commentary_generator import (
    DEFAULT_OLLAMA_HOST,
    DEFAULT_OLLAMA_MODEL,
)
from backend.app.intelligence.embeddings import (
    embed_text,
    embed_texts,
    format_decision_log,
    get_embedding_source,
)
from backend.app.twin.store import store

logger = logging.getLogger(__name__)


class RaceQAEngine:
    """Historical race question-answering system grounded in verified digital twin logs."""

    def __init__(self, model_name: str = DEFAULT_OLLAMA_MODEL, host: str = DEFAULT_OLLAMA_HOST):
        self.model_name = model_name
        self.host = host

    async def retrieve_relevant_decisions(
        self,
        query: str,
        race_id: str | None = None,
        top_k: int = 5,
    ) -> list[tuple[dict[str, Any], float]]:
        """
        Fetches decision logs from store, computes cosine similarities against query embedding,
        and returns the top-k highest scoring decisions with their similarity scores.
        """
        logs = await store.get_persisted_decisions(race_id=race_id)
        if not logs:
            return []

        # If query specifically mentions a lap number like "lap 23" or "lap 5", prioritize exact lap matches
        lap_match = re.search(r"\blap\s*(\d+)\b", query.lower())
        target_lap = int(lap_match.group(1)) if lap_match else None

        texts = [format_decision_log(l) for l in logs]
        log_embeddings = embed_texts(texts)  # [N, dim]
        query_embedding = embed_text(query)  # [dim]

        # Compute cosine similarity
        norm_logs = np.linalg.norm(log_embeddings, axis=1)  # [N]
        norm_query = float(np.linalg.norm(query_embedding))

        # Avoid division by zero
        denom = np.maximum(norm_logs * norm_query, 1e-9)
        raw_similarities = np.dot(log_embeddings, query_embedding) / denom
        similarities = np.atleast_1d(raw_similarities).copy()

        # Boost score if exact lap requested matches
        if target_lap is not None:
            for i, l in enumerate(logs):
                if l.get("lap") == target_lap:
                    similarities[i] += 1.5

        scored_pairs = list(zip(logs, similarities.tolist()))
        scored_pairs.sort(key=lambda p: p[1], reverse=True)

        return scored_pairs[:top_k]

    async def answer_question(
        self,
        query: str,
        race_id: str | None = None,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """
        Main RAG pipeline:
        1. Retrieves top-k matching historical decisions from Postgres/SQLite.
        2. Formats strictly grounded context.
        3. Prompts local LLM (or deterministic fallback) with strict zero-hallucination constraint.
        4. Returns answer along with source citation logs for auditability.
        """
        embedding_source = get_embedding_source()
        scored_results = await self.retrieve_relevant_decisions(query=query, race_id=race_id, top_k=top_k)

        if not scored_results:
            return {
                "answer": "I don't have any decision records in the race history database to answer this query. Please run a race session first.",
                "sources": [],
                "retrieved_count": 0,
                "model_used": "system",
                "embedding_source": embedding_source,
            }

        top_sources = [p[0] for p in scored_results]
        top_scores = [round(p[1], 4) for p in scored_results]

        # Check if the query asks for a lap number that doesn't exist anywhere in the retrieved records
        lap_match = re.search(r"\blap\s*(\d+)\b", query.lower())
        if lap_match:
            requested_lap = int(lap_match.group(1))
            available_laps = {s.get("lap") for s in top_sources}
            if requested_lap not in available_laps:
                return {
                    "answer": f"I don't have that information in the race history logs. No decision log exists for Lap {requested_lap}.",
                    "sources": top_sources,
                    "retrieved_count": len(top_sources),
                    "model_used": "deterministic_grounding",
                    "embedding_source": embedding_source,
                }

        # Build grounded context block
        context_blocks = []
        for i, src in enumerate(top_sources, start=1):
            expl = src.get("explanation_payload") or src.get("decision") or {}
            factors = expl.get("primary_factors", [])
            factors_str = "; ".join(factors) if factors else "Routine stint monitoring"
            context_blocks.append(
                f"[Log {i}] Lap {src.get('lap')}: Directive={src.get('recommendation')} | "
                f"Confidence={int(src.get('confidence_score', 0.85)*100)}% | Urgency={src.get('urgency')} | "
                f"Rule Action={src.get('rule_action')} | DQN Action={src.get('dqn_action')} | "
                f"Tyre Cliff Risk={src.get('tyre_cliff_risk')} | Factors: {factors_str}"
            )
        context_text = "\n".join(context_blocks)

        prompt = (
            "You are the APEX F1 Race Strategy Intelligence Assistant. "
            "Answer the user's question based ONLY on the following real decision log entries. "
            "Do not invent facts, numbers, or details not present in the logs. "
            "If the logs do not contain the answer, say: 'I don't have that information in the race history logs.'\n\n"
            f"=== VERIFIED RACE DECISION LOGS ===\n{context_text}\n\n"
            f"Question: {query}\n"
            "Answer (concise, factual, professional):"
        )

        answer_text, model_used = self._call_llm_or_fallback(prompt, query, top_sources)

        # Sanitize source records for frontend display
        sources_payload = []
        for s, score in zip(top_sources, top_scores):
            expl = s.get("explanation_payload") or s.get("decision") or {}
            sources_payload.append({
                "race_id": s.get("race_id"),
                "lap": s.get("lap"),
                "recommendation": s.get("recommendation"),
                "confidence_score": s.get("confidence_score"),
                "urgency": s.get("urgency"),
                "rule_action": s.get("rule_action"),
                "dqn_action": s.get("dqn_action"),
                "tyre_cliff_risk": s.get("tyre_cliff_risk"),
                "primary_factors": expl.get("primary_factors", []),
                "commentary": expl.get("commentary"),
                "similarity_score": score,
            })

        return {
            "answer": answer_text,
            "sources": sources_payload,
            "retrieved_count": len(sources_payload),
            "model_used": model_used,
            "embedding_source": embedding_source,
        }

    def _call_llm_or_fallback(
        self,
        prompt: str,
        query: str,
        sources: list[dict[str, Any]],
    ) -> tuple[str, str]:
        """Attempts Ollama inference first, falling back to grounded rule extraction."""
        try:
            import ollama
            client = ollama.Client(host=self.host, timeout=2.0)
            response = client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1, "top_p": 0.8},
            )
            ans = response.get("message", {}).get("content", "").strip()
            if ans:
                return ans, f"ollama/{self.model_name}"
        except Exception as e:
            logger.debug(f"[RaceQA] Ollama offline or timed out ({e}). Using deterministic grounding fallback.")

        # Deterministic grounded fallback
        top = sources[0]
        lap = top.get("lap")
        rec = top.get("recommendation")
        conf = int(top.get("confidence_score", 0.85) * 100)
        urgency = top.get("urgency")
        expl = top.get("explanation_payload") or top.get("decision") or {}
        factors = expl.get("primary_factors", [])
        factors_summary = f"driven primarily by {factors[0].lower()}" if factors else "based on stint window progression"

        q_lower = query.lower()
        if "why" in q_lower or "reason" in q_lower:
            ans = f"On Lap {lap}, the decision was {rec} with {conf}% confidence ({urgency} urgency), {factors_summary}."
        elif "recommend" in q_lower or "what did" in q_lower or "action" in q_lower:
            ans = f"On Lap {lap}, APEX recommended {rec} with {conf}% confidence ({urgency} urgency). Top factor: {factors[0] if factors else 'Tyre degradation management'}."
        elif "dqn" in q_lower or "safety car" in q_lower:
            ans = f"On Lap {lap}, the DQN RL agent proposed {top.get('dqn_action', rec)} while the rule engine baseline was {top.get('rule_action', rec)} (Cliff risk: {top.get('tyre_cliff_risk', 'LOW')})."
        else:
            ans = f"According to Lap {lap} logs: Directive was {rec} ({conf}% confidence, {urgency} urgency). {factors_summary.capitalize()}."

        return ans, "deterministic_grounded_fallback"


# Singleton instance
race_qa_engine = RaceQAEngine()


async def answer_race_question(
    query: str,
    race_id: str | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    """Helper to query race decision history via RAG."""
    return await race_qa_engine.answer_question(query=query, race_id=race_id, top_k=top_k)
