from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any
from rebound.models import Cause, Classification, PaymentFailure

_VALID_CAUSES = {c.value for c in Cause}

_PROMPT = """You are classifying why a recurring payment failed, into exactly one of these causes:
insufficient_funds, instrument_expired_or_blocked, authentication_failed, bank_or_gateway_error,
mandate_not_active, limit_exceeded, unknown.

Use ONLY the free-text description below; do not invent details. If the description is too vague
to be confident, return "unknown" with low confidence rather than guessing.

Description: {description}

Respond with ONLY a JSON object: {{"cause": "<one of the causes above>", "confidence": <0.0-1.0>, "rationale": "<one sentence>"}}"""


class LLMClassifier:
    def __init__(self, client: Any, cache_dir: Path, confidence_threshold: float = 0.75,
                 model: str = "claude-sonnet-5") -> None:
        self.client = client
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.threshold = confidence_threshold
        self.model = model

    def _cache_key(self, pf: PaymentFailure) -> Path:
        h = hashlib.sha256(pf.model_dump_json().encode("utf-8")).hexdigest()
        return self.cache_dir / f"{h}.json"

    def classify(self, pf: PaymentFailure) -> Classification:
        cache_path = self._cache_key(pf)
        if cache_path.exists():
            raw = json.loads(cache_path.read_text())
        else:
            prompt = _PROMPT.format(description=pf.error_description or "")
            response = self.client.messages.create(
                model=self.model, max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text
            raw = json.loads(text)
            cache_path.write_text(json.dumps(raw))

        cause_str = raw.get("cause", "unknown")
        confidence = float(raw.get("confidence", 0.0))
        rationale = raw.get("rationale")

        if cause_str not in _VALID_CAUSES or confidence < self.threshold:
            return Classification(cause=Cause.UNKNOWN, provenance="abstain",
                                   confidence=confidence, rationale=rationale)
        return Classification(cause=Cause(cause_str), provenance="llm",
                               confidence=confidence, rationale=rationale)
