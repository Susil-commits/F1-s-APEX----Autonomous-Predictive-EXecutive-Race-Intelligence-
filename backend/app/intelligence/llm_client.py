"""Unified Multi-Tier LLM Client for APEX Intelligence.

Supports Cloud Inference (Groq / OpenAI-compatible APIs) with fallback to
local Ollama and offline deterministic persona engines.
"""
import logging
import os
import time
import unicodedata
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Cloud Provider Settings
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "groq/compound-mini")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions")

# Local Ollama Settings
DEFAULT_OLLAMA_MODEL = os.getenv("APEX_OLLAMA_MODEL", "llama3.2:3b")
DEFAULT_OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Circuit breaker state for Ollama
_ollama_available: Optional[bool] = None
_last_ollama_check: float = 0.0
_OLLAMA_RETRY_INTERVAL: float = 60.0


def _sanitize_text(text: str) -> str:
    """Normalizes Unicode non-breaking spaces/hyphens and smart quotes to standard characters."""
    if not text:
        return text
    cleaned = (
        text.replace("\u2011", "-")
        .replace("\u2012", "-")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u00a0", " ")
    )
    return unicodedata.normalize("NFKD", cleaned)


def _get_groq_provider_name(model_name: str) -> str:
    if model_name.startswith("groq/"):
        return model_name
    return f"groq/{model_name}"


def call_llm_sync(
    prompt: str,
    system_prompt: str = "You are the APEX F1 Race Strategy Intelligence Assistant.",
    temperature: float = 0.15,
    max_tokens: int = 256,
    timeout: float = 8.0,
) -> tuple[Optional[str], str]:
    """Synchronous multi-tier LLM invocation: Groq -> OpenAI -> Ollama -> None."""
    global _ollama_available, _last_ollama_check

    # Tier 1: Groq Cloud API (Free, ultrafast Llama 3.3 / Compound / Qwen)
    if GROQ_API_KEY.strip():
        try:
            with httpx.Client(timeout=timeout) as client:
                res = client.post(
                    GROQ_API_URL,
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY.strip()}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": GROQ_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    content = _sanitize_text(data["choices"][0]["message"]["content"].strip())
                    return content, _get_groq_provider_name(GROQ_MODEL)
                else:
                    logger.warning(f"[APEX LLM] Groq API returned status {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"[APEX LLM] Groq cloud inference error: {e}")

    # Tier 2: OpenAI / Custom OpenAI-compatible Cloud API
    if OPENAI_API_KEY.strip():
        try:
            with httpx.Client(timeout=timeout) as client:
                res = client.post(
                    OPENAI_BASE_URL,
                    headers={
                        "Authorization": f"Bearer {OPENAI_API_KEY.strip()}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": OPENAI_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    content = _sanitize_text(data["choices"][0]["message"]["content"].strip())
                    return content, f"openai/{OPENAI_MODEL}"
        except Exception as e:
            logger.warning(f"[APEX LLM] OpenAI cloud inference error: {e}")

    # Tier 3: Local Ollama (Local desktop runtime)
    now = time.time()
    if _ollama_available is False and (now - _last_ollama_check < _OLLAMA_RETRY_INTERVAL):
        return None, "fallback"

    try:
        import ollama
        client = ollama.Client(host=DEFAULT_OLLAMA_HOST, timeout=0.8)
        response = client.chat(
            model=DEFAULT_OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            options={"temperature": temperature, "top_p": 0.9},
        )
        _ollama_available = True
        raw_text = _sanitize_text(response.get("message", {}).get("content", "").strip())
        if raw_text:
            return raw_text, f"ollama/{DEFAULT_OLLAMA_MODEL}"
    except Exception as e:
        _ollama_available = False
        _last_ollama_check = now
        logger.debug(f"[APEX LLM] Local Ollama offline ({e}).")

    return None, "fallback"


async def call_llm_async(
    prompt: str,
    system_prompt: str = "You are the APEX F1 Race Strategy Intelligence Assistant.",
    temperature: float = 0.15,
    max_tokens: int = 350,
    timeout: float = 10.0,
) -> tuple[Optional[str], str]:
    """Asynchronous multi-tier LLM invocation: Groq -> OpenAI -> Ollama -> None."""
    global _ollama_available, _last_ollama_check

    # Tier 1: Groq Cloud API
    if GROQ_API_KEY.strip():
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(
                    GROQ_API_URL,
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY.strip()}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": GROQ_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    content = _sanitize_text(data["choices"][0]["message"]["content"].strip())
                    return content, _get_groq_provider_name(GROQ_MODEL)
                else:
                    logger.warning(f"[APEX LLM] Groq async API returned status {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"[APEX LLM] Groq async cloud inference error: {e}")

    # Tier 2: OpenAI Cloud API
    if OPENAI_API_KEY.strip():
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(
                    OPENAI_BASE_URL,
                    headers={
                        "Authorization": f"Bearer {OPENAI_API_KEY.strip()}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": OPENAI_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    content = _sanitize_text(data["choices"][0]["message"]["content"].strip())
                    return content, f"openai/{OPENAI_MODEL}"
        except Exception as e:
            logger.warning(f"[APEX LLM] OpenAI async cloud inference error: {e}")

    # Tier 3: Local Ollama (run in threadpool/sync)
    now = time.time()
    if _ollama_available is False and (now - _last_ollama_check < _OLLAMA_RETRY_INTERVAL):
        return None, "fallback"

    try:
        import ollama
        client = ollama.Client(host=DEFAULT_OLLAMA_HOST, timeout=1.5)
        response = client.chat(
            model=DEFAULT_OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            options={"temperature": temperature, "top_p": 0.9},
        )
        _ollama_available = True
        raw_text = _sanitize_text(response.get("message", {}).get("content", "").strip())
        if raw_text:
            return raw_text, f"ollama/{DEFAULT_OLLAMA_MODEL}"
    except Exception as e:
        _ollama_available = False
        _last_ollama_check = now
        logger.debug(f"[APEX LLM] Local Ollama offline ({e}).")

    return None, "fallback"
