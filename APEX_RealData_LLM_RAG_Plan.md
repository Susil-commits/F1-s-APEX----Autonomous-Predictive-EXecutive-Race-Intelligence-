# APEX — Real Data, LLM Commentary & RAG: Implementation Plan

*Hand this whole document to your coding agent as the spec. Each section is self-contained: what to build, where, using what data source, and how to verify it actually worked (not just runs without crashing).*

---

## PART 1 — Calibrate Tyre Model on Real F1 Data

### What this is
Replace/augment the synthetic tyre-wear training data with real historical race data, so the tyre degradation model's predictions are grounded in reality instead of a hand-written formula.

### Where to find the data
**Package: `fastf1`** (`pip install fastf1`) — wraps the official F1 timing API. Free, no API key required for basic session data, actively maintained.

```python
import fastf1
fastf1.Cache.enable_cache('backend/data/fastf1_cache')  # required, or it re-downloads every run
session = fastf1.get_session(2023, 'Silverstone', 'R')  # year, event, session type ('R' = race)
session.load()
laps = session.laps  # DataFrame: LapTime, Compound, TyreLife, Stint, Driver, TrackStatus, etc.
```

Pull **3-5 real races** across different circuits (Silverstone, Monza, Spa — tracks you already model) and 2-3 different seasons for variety. Each race gives hundreds of laps of real (compound, tyre_age, lap_time_delta) triples.

### What to build

**New file: `backend/training/fetch_fastf1_data.py`**
- Downloads N specified races via `fastf1.get_session(...)`, caches locally (`backend/data/fastf1_cache/`, add to `.gitignore` — this cache gets large).
- Extracts per-lap: `Compound`, `TyreLife` (laps on that tyre), `LapTime` (convert to seconds), `Stint`, and computes `lap_time_delta` = lap time minus that driver's fastest lap of the session (isolates degradation from raw pace differences between drivers).
- Filters out in/out laps (pit laps), safety car laps (`TrackStatus` flags), and outliers (first-lap tyre warm-up, red flags) — raw data is noisy, needs cleaning before it's usable.
- Saves cleaned dataset to `backend/data/real_tyre_data.csv`.

**Edit: wherever your tyre degradation model is currently trained** (locate the tyre model training/fitting code — likely near `backend/app/intelligence/` alongside `feature_builder.py`, or check for a `tyre_model.py`)
- Add a `--real-data` flag: if `backend/data/real_tyre_data.csv` exists, train against it (compound, tyre age → lap time delta) instead of / in addition to the synthetic simulator-generated data.
- Keep the synthetic fallback — same pattern as the SHAP surrogate's graceful fallback. Don't delete the synthetic path, just prefer real data when available.

**New file: `backend/training/validate_tyre_model.py`**
- Holds out one race's data, trains on the rest, predicts degradation curve for the held-out race, plots predicted vs. actual (same style as `training_rewards.png`), saves `backend/models/tyre_model_validation.png`.
- Reports R², RMSE — same honest-metrics pattern as the SHAP distillation metadata.

### How to verify it worked
- The validation plot should show predicted degradation reasonably tracking actual degradation (not perfect — real races have SC periods, fuel effect, driver variance — but the *shape* of the curve should match).
- Compare the new model's R² against a naive baseline (e.g., "assume linear wear") — if your model isn't beating a straight line, something's wrong.
- **Don't claim more than the data supports.** If R² is 0.5-0.6, that's a legitimate result for real-world messy data — say that honestly rather than only training/reporting on the easiest race.

---

## PART 2 — LLM Race Engineer Commentary

### What this is
Turn your existing `DecisionExplanation` object (recommendation, confidence, SHAP factors, urgency) into a natural-language line, like a real race engineer talking over the radio — without letting the LLM make any actual decisions.

### Where to find the model
Use a **local model via Ollama** — zero API cost, no key required, runs on your machine, works offline for demos (important: you don't want your portfolio demo to break because an API key expired or rate-limited during an interview).

- Install Ollama, pull a small instruction-tuned model: `ollama pull llama3.2:3b` (small enough to run fast on a laptop, good enough for this templated task).
- Python client: `pip install ollama`, then `ollama.chat(model='llama3.2:3b', messages=[...])`.

If you'd rather use a hosted API instead (Claude/OpenAI), that's fine too — same integration point, just swap the client call. Local is recommended specifically so your demo never depends on an internet connection or a live key during an interview.

### What to build

**New file: `backend/app/intelligence/commentary_generator.py`**
- Function `generate_commentary(explanation: DecisionExplanation) -> str`.
- Builds a tightly constrained prompt: feed it the recommendation, top 2-3 SHAP factors, urgency, confidence — explicitly instruct it to **only rephrase what's given, never invent numbers or reasoning not present in the input.** This is the important part — the LLM is a translator, not a decision-maker.
- Example prompt shape:
  ```
  You are an F1 race engineer speaking over team radio. Given this strategy
  decision, say ONE short radio-style line (under 20 words). Use ONLY the
  facts given. Do not invent numbers.

  Decision: {recommendation}
  Confidence: {confidence_score}
  Urgency: {urgency}
  Top factors: {top 2-3 SHAP feature names + direction}
  ```
- Wrap in try/except with a **template-based fallback** (e.g., an f-string like `f"Box, box — {top_factor} is the call."`) if Ollama isn't running or times out. Same graceful-degradation pattern as your Redis/SHAP fallbacks — this is now a consistent architectural signature across your project, worth keeping it that way.
- Cache/debounce: don't call the LLM every single tick (52 laps × however many ticks = a lot of calls for not much benefit) — only generate new commentary when the recommendation actually changes, or every N laps.

**Edit: `backend/app/api/websocket.py`**
- In `_enrich_state`, after building the `explanation`, call `generate_commentary(explanation)` and attach it as `state.active_decision.commentary` (or a new field) before `store.log_decision(...)`.

**Frontend:** add a small "Race Engineer" text/audio-style panel that displays the latest commentary line — you already have an audio DSP/voice persona layer built, so this may slot into existing UI rather than needing new components. Check what's there before building new.

### How to verify it worked
- Test that commentary text never contains a number that isn't in the input `DecisionExplanation` (spot-check a handful, or write an assertion that flags standalone numbers in the LLM output not present in the prompt's facts).
- Test the fallback path explicitly (mock Ollama to raise, confirm the template fallback fires and the app doesn't crash).
- Write `backend/tests/test_commentary_generator.py` — this project has a good habit of testing fallback paths now (see the SHAP/Redis tests), keep that up here too.

---

## PART 3 — RAG Over Your Own Race History

### What this is
Let someone ask natural-language questions about past races run in this system ("why did we pit on lap 23," "how did the DQN handle the safety car") and get an answer grounded in your actual logged `DecisionLogModel` rows in Postgres — not a generic LLM guess.

### Where to find the data
You already have it: `DecisionLogModel` (race_id, lap, recommendation, confidence, urgency, SHAP-linked factors, explanation payload) has been persisting every real decision since Part 3 of your earlier build. This is genuine project-specific data, not an external dataset — which is exactly what makes RAG here honest rather than decorative.

### What to build

**New file: `backend/app/intelligence/embeddings.py`**
- Use `sentence-transformers` (`pip install sentence-transformers`, model: `all-MiniLM-L6-v2` — small, fast, runs locally, no API cost) to embed a text representation of each decision log entry (e.g., `"Lap 23: recommended PIT_HARD, urgency HIGH, driven by tyre wear 82% and rain probability 0.4"`).
- Function `embed_decision_log(entry: dict) -> np.ndarray`.

**New file: `backend/app/intelligence/race_qa.py`**
- On startup (or lazily on first query), pull all `DecisionLogModel` rows for a given race (or all races) via `store.get_persisted_session_ticks`-style query, embed each one, hold them in memory as a numpy array. **Don't reach for a dedicated vector DB (Pinecone/Chroma/etc.) — with a few hundred to a few thousand rows, brute-force cosine similarity in numpy is faster to build, easier to explain in an interview, and completely sufficient.** Only mention this as future scaling if asked.
- Function `answer_race_question(query: str, race_id: Optional[str] = None) -> str`:
  1. Embed the query.
  2. Cosine-similarity against stored decision embeddings, take top-k (e.g., 5).
  3. Feed those k real decision log entries + the question to the LLM (same Ollama setup as Part 2), instructed to answer **only from the provided entries** and say "I don't have that information" if the retrieved entries don't cover it.
- This reuses the same LLM client from Part 2 — don't duplicate the Ollama wiring, share it.

**New endpoint: `backend/app/api/routes.py`**
- `POST /api/race/ask` — takes `{race_id, question}`, calls `answer_race_question`, returns the answer plus the retrieved source decision entries (so the frontend/user can see what it was grounded in — this is the "citations" equivalent for your own RAG, and it's the difference between "trust me" and "here's what I found").

**Frontend:** simple chat-style input box, probably a new small component, e.g. `RaceHistoryQA.tsx`.

### How to verify it worked
- Ask a question with a clear factual answer that exists in the logs ("what did we recommend on lap 23") and confirm the answer matches the actual logged entry, not a hallucination.
- Ask a question with **no** matching data (e.g., about a lap number that doesn't exist) and confirm it says it doesn't know, rather than inventing an answer.
- `backend/tests/test_race_qa.py`: seed a few known `DecisionLogModel` rows, ask a question that should retrieve one specific entry, assert that entry is in the top-k retrieved (don't need to assert on LLM phrasing, just retrieval correctness — that's the part that's actually testable deterministically).

---

## Build Order & Dependencies

1. **Part 1 first, standalone** — no dependency on the other two, and it strengthens something you're already claiming (tyre model realism).
2. **Part 2 second** — needed before Part 3, since Part 3 reuses its Ollama client.
3. **Part 3 last** — depends on Part 2's LLM wiring and on having a decent number of logged decisions already in Postgres (run a few races first so there's something to retrieve).

## New dependencies to add to `pyproject.toml`
```
fastf1>=3.3.0
ollama>=0.3.0
sentence-transformers>=3.0.0
```

## One instruction to give your agent up front, given this project's history

This repo has a track record of shipping a plausible-looking version of a feature first (fake SHAP, fake Monte Carlo) that needed a second pass to become real. Tell your agent explicitly, for all three parts above: **implement the real, grounded version on the first pass — no placeholder/synthetic version that "looks like" it works. If real data or a local model isn't available in the dev environment, fail loudly with a clear error rather than silently substituting fabricated output.** The one exception is the LLM commentary's *template fallback* in Part 2 — that one is fine and intentional, because it's an honest, clearly-labeled degradation path, not a disguised fake.
