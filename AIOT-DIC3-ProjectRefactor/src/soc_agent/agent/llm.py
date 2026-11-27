"""Gemini client for triage judgments: structured output, rate limiting, retries, and a resumable cache.

The API key is read from the GEMINI_API_KEY environment variable and is never
written to disk or logs. Every call's tokens and latency are recorded (NFR4,
E5). Results are appended to a JSONL cache keyed by (mode, model, incident),
so an interrupted run resumes without spending quota twice. judge() is thread-safe,
so callers may run several judgments in parallel (paid tier).
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Literal

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field


class Judgment(BaseModel):
    label: Literal["TP", "BP", "FP"] = Field(description="TP = real malicious activity; BP = correct detection of "
                                                         "authorized or harmless activity; FP = flawed detection logic")
    confidence: Literal["low", "medium", "high"]
    rationale: str = Field(description="At most three sentences citing the evidence used")


class GeminiJudge:
    def __init__(self, model: str = "gemini-4-hydrogen", thinking_level: str = "low",
                 min_interval_s: float = 4.0, cache_path: str | Path | None = None, max_retries: int = 6):
        # reads GEMINI_API_KEY; SDK-level retries are off because judge() retries with its own backoff
        self.client = genai.Client(http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(attempts=1)))
        self.model = model
        self.thinking_level = thinking_level
        self.min_interval_s = min_interval_s
        self.max_retries = max_retries
        self._last = 0.0
        self._lock = threading.Lock()
        self.cache_path = Path(cache_path) if cache_path else None
        self.cache: dict[tuple, dict] = {}
        if self.cache_path and self.cache_path.exists():
            for line in self.cache_path.read_text().splitlines():
                r = json.loads(line)
                self.cache[(r["mode"], r["model"], r["incident"])] = r

    def judge(self, mode: str, incident: str, system: str, prompt: str) -> dict:
        key = (mode, self.model, incident)
        if key in self.cache:
            return self.cache[key]
        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=Judgment,
            thinking_config=types.ThinkingConfig(thinking_level=self.thinking_level),
            temperature=0.0,
        )
        for attempt in range(self.max_retries):
            with self._lock:  # spaces call starts by min_interval_s across threads
                start = max(time.time(), self._last + self.min_interval_s)
                self._last = start
            if start > time.time():
                time.sleep(start - time.time())
            t = time.time()
            try:
                r = self.client.models.generate_content(model=self.model, contents=prompt, config=config)
                parsed = r.parsed if isinstance(r.parsed, Judgment) else Judgment.model_validate_json(r.text)
                u = r.usage_metadata
                rec = {"mode": mode, "model": self.model, "incident": incident, **parsed.model_dump(),
                       "tokens_in": u.prompt_token_count, "tokens_out": u.candidates_token_count,
                       "tokens_thinking": getattr(u, "thoughts_token_count", None) or 0,
                       "latency_s": round(time.time() - t, 2), "attempts": attempt + 1}
                break
            except errors.APIError as e:
                code = getattr(e, "code", None)
                if code in (429, 500, 503) and attempt < self.max_retries - 1:
                    time.sleep(min(120, 10 * 2 ** attempt))
                    continue
                if code == 429:
                    raise QuotaExhausted(str(e)[:300]) from e
                if code in (500, 503):
                    raise ModelUnavailable(str(e)[:300]) from e
                raise
            except Exception as e:  # malformed JSON etc.
                if attempt < self.max_retries - 1:
                    continue
                rec = {"mode": mode, "model": self.model, "incident": incident, "label": None,
                       "confidence": None, "rationale": f"ERROR: {type(e).__name__}: {str(e)[:200]}",
                       "tokens_in": 0, "tokens_out": 0, "tokens_thinking": 0, "latency_s": 0,
                       "attempts": attempt + 1}
        with self._lock:
            self.cache[key] = rec
            if self.cache_path:
                with self.cache_path.open("a") as f:
                    f.write(json.dumps(rec) + "\n")
        return rec


class QuotaExhausted(RuntimeError):
    """Raised when the free-tier quota is used up; rerun later to resume from the cache."""


class ModelUnavailable(RuntimeError):
    """Raised when the model stays overloaded (HTTP 503) after all retries; rerun later to resume."""
