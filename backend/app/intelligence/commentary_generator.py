"""LLM Race Engineer Commentary Generator for APEX Decision Intelligence.

Converts structured DecisionExplanation telemetry attributions into authentic F1 team radio
transmissions using local LLMs (Ollama) with strict zero-hallucination fact constraints
and persona-based template fallbacks.
"""
import logging
import os
import re
import time

from backend.app.simulator.models import DecisionExplanation

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_MODEL = os.getenv("APEX_OLLAMA_MODEL", "llama3.2:3b")
DEFAULT_OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


class CommentaryGenerator:
    """Translates strategy decisions into natural language team radio transmissions.
    
    The LLM functions strictly as a translator/summarizer, never as a decision-maker.
    """

    _ollama_available: bool | None = None
    _last_ollama_check: float = 0.0
    _OLLAMA_RETRY_INTERVAL: float = 60.0

    def __init__(self, model_name: str = DEFAULT_OLLAMA_MODEL, host: str = DEFAULT_OLLAMA_HOST):
        self.model_name = model_name
        self.host = host
        self._last_recommendation: str | None = None
        self._last_urgency: str | None = None
        self._last_lap_generated: int = -99
        self._cached_commentary: str | None = None
        self._last_call_time: float = 0.0

    def generate(
        self,
        explanation: DecisionExplanation,
        current_lap: int = 1,
        persona: str = "apex_core",
        force_refresh: bool = False,
    ) -> str:
        """
        Generates a concise radio transmission line (under 20 words) for the active decision.
        Debounces across identical ticks unless recommendation changes or every 5 laps.
        """
        rec_str = str(explanation.recommendation.value if hasattr(explanation.recommendation, "value") else explanation.recommendation)
        urgency_str = explanation.urgency

        # Debounce check
        rec_changed = (rec_str != self._last_recommendation)
        urgency_changed = (urgency_str != self._last_urgency)
        lap_gap = current_lap - self._last_lap_generated

        if not force_refresh and not rec_changed and not urgency_changed and lap_gap < 5 and self._cached_commentary:
            return self._cached_commentary

        # Format prompt facts
        top_factors = explanation.primary_factors[:3] if explanation.primary_factors else ["Tyre degradation management"]
        factors_summary = "; ".join(top_factors)
        conf_pct = int(explanation.confidence_score * 100)

        prompt = (
            "You are an F1 race engineer speaking over team radio. Given this strategy decision, "
            "say ONE short radio-style line (under 20 words). Use ONLY the facts given. "
            "Do not invent numbers or add facts not provided.\n\n"
            f"Decision: {rec_str}\n"
            f"Confidence: {conf_pct}%\n"
            f"Urgency: {urgency_str}\n"
            f"Top factors: {factors_summary}\n"
            f"Tyre cliff risk: {explanation.tyre_cliff_risk}\n"
            f"Pit window status: {explanation.pit_window_status}\n"
        )

        commentary = self._call_llm_or_fallback(prompt, explanation, persona)

        # Strip extraneous quotes and markdown wrappers
        commentary = commentary.strip(' \n\r\t"\'`')
        if commentary.startswith("Radio:") or commentary.startswith("Engineer:"):
            commentary = commentary.split(":", 1)[1].strip()

        # Update cache state
        self._last_recommendation = rec_str
        self._last_urgency = urgency_str
        self._last_lap_generated = current_lap
        self._cached_commentary = commentary
        self._last_call_time = time.time()

        return commentary

    def _call_llm_or_fallback(
        self,
        prompt: str,
        explanation: DecisionExplanation,
        persona: str = "apex_core",
    ) -> str:
        """Invokes multi-tier LLM (Groq cloud -> OpenAI -> local Ollama), falling back to persona template."""
        from backend.app.intelligence.llm_client import call_llm_sync

        system_prompt = (
            "You are an F1 race engineer speaking over team radio. "
            "Say ONE concise radio transmission line (under 20 words) based strictly on verified strategy telemetry."
        )
        raw_text, provider = call_llm_sync(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.15,
            max_tokens=64,
            timeout=8.0,
        )

        if raw_text:
            if self.is_fact_consistent(raw_text, explanation):
                return raw_text
            else:
                logger.warning(f"[Commentary] {provider} violated fact constraints: '{raw_text}'. Using fallback template.")

        return self.get_template_fallback(explanation, persona)

    @staticmethod
    def get_template_fallback(explanation: DecisionExplanation, persona: str = "apex_core") -> str:
        """
        Deterministic, authentic persona-aligned radio template fallback.
        Ensures 100% reliability even when running fully offline without Ollama.
        """
        rec = str(explanation.recommendation.value if hasattr(explanation.recommendation, "value") else explanation.recommendation)
        factor = explanation.primary_factors[0] if explanation.primary_factors else "strategic window"
        conf = int(explanation.confidence_score * 100)

        is_pit = rec.startswith("PIT_")

        if persona == "bono":
            if is_pit:
                return f"Box box, box this lap. {rec.replace('PIT_', '')} tyres ready. Hammer time."
            if rec == "PUSH":
                return "Strat mode 2, Lewis. Let's push now."
            if rec == "CONSERVE":
                return "Manage the front tyres, Lewis. Pace looks good."
            return f"Keep your head down, {factor.lower()} is looking solid."

        elif persona == "gp":
            if is_pit:
                return f"Pit confirm, Max. Box this lap for {rec.replace('PIT_', '')}s."
            if rec == "PUSH":
                return "Unleash the pace, Max. Push now."
            if rec == "CONSERVE":
                return "Watch tyre temps in sector 2, manage the delta."
            return "Pace is strong. Maintaining current stint."

        elif persona == "xavi":
            if is_pit:
                return f"Box this lap for {rec.replace('PIT_', '')}, box now. Confirm."
            if rec == "PUSH":
                return "Push now, mode push. We are fighting."
            if rec == "CONSERVE":
                return "We are checking tyre wear. Conserve mode on."
            return "Stay out, Plan A is working. We are checking."

        elif persona == "guenther":
            if is_pit:
                return f"Gene, box this lap for {rec.replace('PIT_', '')}s. Let's look like rockstars."
            if rec == "PUSH":
                return "Push like hell now. Give it everything."
            if rec == "CONSERVE":
                return "Look after the tyres. We cannot afford mistakes."
            return "Pace is consistent, keep the car clean."

        elif persona == "hugh_bird":
            if is_pit:
                return f"Box this lap, Checo. Fitting {rec.replace('PIT_', '')}s."
            if rec == "PUSH":
                return "Mode overtake available, let's close the gap."
            if rec == "CONSERVE":
                return "Manage the rear tyres on exit, delta is good."
            return "Good pace, stint target on track."

        elif persona == "ricky":
            if is_pit:
                return f"Box now, Carlos. Box for {rec.replace('PIT_', '')}s. Push in lap."
            if rec == "PUSH":
                return "Smooth operator mode, push now Carlos."
            if rec == "CONSERVE":
                return "Conserve the fronts in high speed, manage tyres."
            return "Strategy is working, Carlos. Stint looks good."

        # Default: apex_core
        if is_pit:
            comp = rec.replace("PIT_", "")
            return f"Box, box this lap for {comp}s — {factor.lower()}."
        if rec == "PUSH":
            return f"Push now. {conf}% confidence on pace advantage."
        if rec == "CONSERVE":
            return "Tyre management call: conserve stint to protect cliff margin."
        return f"Maintain stint. {factor} is optimal."

    @staticmethod
    def is_fact_consistent(text: str, explanation: DecisionExplanation) -> bool:
        """
        Validates that generated text does not hallucinate arbitrary numerical metrics
        that were not present in the input explanation.
        """
        # Extract standalone integers or floats from text
        numbers_in_text = re.findall(r"\b\d+(?:\.\d+)?\b", text)
        if not numbers_in_text:
            return True

        # Collect all valid numbers in the explanation payload
        valid_numbers = set()
        conf_int = int(explanation.confidence_score * 100)
        valid_numbers.add(str(conf_int))
        valid_numbers.add(f"{explanation.confidence_score:.2f}")

        if explanation.expected_time_delta_s is not None:
            valid_numbers.add(str(abs(int(explanation.expected_time_delta_s))))
            valid_numbers.add(f"{abs(explanation.expected_time_delta_s):.1f}")
            valid_numbers.add(f"{abs(explanation.expected_time_delta_s):.2f}")

        # Check factors text for numbers
        for factor in explanation.primary_factors:
            for num in re.findall(r"\b\d+(?:\.\d+)?\b", factor):
                valid_numbers.add(num)
                try:
                    valid_numbers.add(str(int(float(num))))
                except ValueError:
                    pass

        # Allow benign common radio numbers (e.g. '1' in Plan 1 or Box 1, '2' in Strat 2, '3' in Box Box Box)
        benign_radio_numbers = {"1", "2", "3"}

        for num in numbers_in_text:
            if num in benign_radio_numbers or num in valid_numbers:
                continue
            # If an unexplained number > 4 appears (e.g. hallucinating lap 45 or 82% wear), flag it
            try:
                val = float(num)
                if val > 3.0:
                    return False
            except ValueError:
                pass

        return True


# Singleton instance
commentary_generator = CommentaryGenerator()


def generate_commentary(
    explanation: DecisionExplanation,
    current_lap: int = 1,
    persona: str = "apex_core",
) -> str:
    """Module-level helper to generate race engineer radio commentary."""
    return commentary_generator.generate(explanation, current_lap=current_lap, persona=persona)
