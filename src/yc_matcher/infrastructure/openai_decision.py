from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from ..application.ports import DecisionPort, LoggerPort
from ..domain.entities import Criteria, Profile


class OpenAIDecisionAdapter(DecisionPort):
    """DecisionPort implementation backed by an OpenAI-like client.

    The client must expose a `responses.create(...)` method and return an object with:
      - `.output` or `.output_text` yielding a dict-like schema
      - optional `.usage` with `input_tokens` and `output_tokens`
    This keeps the adapter testable without requiring the real SDK.
    """

    def __init__(
        self,
        client: Any,
        logger: LoggerPort | None = None,
        model: str | None = None,
        prompt_ver: str = "v1",
        rubric_ver: str = "v1",
    ) -> None:
        self.client = client
        self.logger = logger
        self.model = model or os.getenv("OPENAI_DECISION_MODEL", "gpt-decide-mock")
        self.prompt_ver = prompt_ver
        self.rubric_ver = rubric_ver

    def _log_usage(self, resp: Any) -> None:
        if not self.logger:
            return
        usage = getattr(resp, "usage", None)
        if isinstance(usage, dict):
            inp = int(usage.get("input_tokens", 0))
            out = int(usage.get("output_tokens", 0))
        else:
            # tolerant extraction from attributes
            inp = int(getattr(usage, "input_tokens", 0) or 0) if usage else 0
            out = int(getattr(usage, "output_tokens", 0) or 0) if usage else 0
        cost_est = (inp * 0.003 / 1000.0) + (out * 0.012 / 1000.0) if (inp or out) else 0.0
        self.logger.emit(
            {
                "event": "model_usage",
                "model": self.model,
                "tokens_in": inp,
                "tokens_out": out,
                "cost_est": round(cost_est, 6),
                "prompt_ver": self.prompt_ver,
                "rubric_ver": self.rubric_ver,
            }
        )

    def evaluate(self, profile: Profile, criteria: Criteria) -> Mapping[str, Any]:
        sys_prompt = (
            f"You are a decisioning function. Return a JSON object with keys: "
            f"decision (YES|NO), rationale (one sentence), draft (string), extracted.name. "
            f"Follow rubric version {self.rubric_ver}."
        )
        user_text = (
            f"Criteria:\n{criteria.text}\n\nProfile:\n{profile.raw_text}\n\n"
            "Decide YES or NO and include a short rationale and a draft outreach using the template rules."
        )
        # Call the client in a library-agnostic way
        resp = self.client.responses.create(model=self.model, input=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_text}],)
        # Extract a dict payload
        payload: dict[str, Any] | None = None
        if hasattr(resp, "output") and isinstance(resp.output, dict):
            payload = resp.output
        elif hasattr(resp, "output_text"):
            maybe = resp.output_text
            if isinstance(maybe, dict):
                payload = maybe
        if not isinstance(payload, dict):
            # Fallback: empty decision
            payload = {"decision": "NO", "rationale": "unparseable", "draft": ""}

        # Stamp versions to the payload for downstream use
        payload.setdefault("prompt_ver", self.prompt_ver)
        payload.setdefault("rubric_ver", self.rubric_ver)

        # Log usage if present
        self._log_usage(resp)

        return payload
