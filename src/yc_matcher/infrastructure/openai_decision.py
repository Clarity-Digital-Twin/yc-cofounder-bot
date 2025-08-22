from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .. import config
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
        # Use model parameter or config function
        self.model = model or config.get_decision_model()
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
        import json

        # Extract template from criteria if present
        template = ""
        if "\nMessage Template:" in criteria.text:
            parts = criteria.text.split("\nMessage Template:")
            criteria_text = parts[0]
            template = parts[1].strip()
        else:
            criteria_text = criteria.text

        sys_prompt = (
            "You are an expert recruiter evaluating potential co-founder matches. "
            "You will analyze a candidate profile against specific criteria and make a decision. "
            "You MUST return a valid JSON object with these exact keys:\n"
            "- decision: string 'YES' or 'NO'\n"
            "- rationale: string explaining your reasoning in 1-2 sentences\n"
            "- draft: if YES, a personalized message to the candidate (if NO, empty string)\n"
            "- score: float between 0.0 and 1.0 indicating match strength\n"
            "- confidence: float between 0.0 and 1.0 indicating your confidence\n\n"
            "Be specific and reference actual details from their profile in the draft message.\n"
            "Your entire response must be valid JSON - no other text before or after the JSON object."
        )

        user_text = f"MY CRITERIA:\n{criteria_text}\n\nCANDIDATE PROFILE:\n{profile.raw_text}\n\n"

        if template:
            user_text += f"MESSAGE TEMPLATE (use this style but personalize it):\n{template}\n\n"

        user_text += (
            "Evaluate if this candidate matches my criteria. "
            "If YES, write a personalized outreach message that references specific details from their profile. "
            "Make the message feel genuine and not like a template."
        )

        # Use the correct OpenAI chat completions API
        try:
            # Use Responses API for GPT-5, Chat Completions for GPT-4
            if self.model.startswith("gpt-5"):
                # Note: Responses API doesn't support response_format parameter
                # We instruct JSON format in the prompt instead
                resp = self.client.responses.create(
                    model=self.model,
                    input=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_text + "\n\nIMPORTANT: Return your response as valid JSON."},
                    ],
                    max_output_tokens=800,  # Responses API uses max_output_tokens
                )
                # Extract content from Responses API format
                content = resp.output_text if hasattr(resp, 'output_text') else str(resp.output[0])
            else:
                # Fallback to Chat Completions for GPT-4 and older
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_text},
                    ],
                    response_format={"type": "json_object"},  # Force JSON response
                    temperature=0.7,  # Some creativity for message drafting
                    max_tokens=800,  # Enough for decision + message
                )
                # Parse the JSON response
                content = resp.choices[0].message.content
            payload = json.loads(content)

            # Ensure required fields
            if "decision" not in payload:
                payload["decision"] = "NO"
            if "rationale" not in payload:
                payload["rationale"] = "No rationale provided"
            if "draft" not in payload:
                payload["draft"] = ""
            if "score" not in payload:
                payload["score"] = 0.5
            if "confidence" not in payload:
                payload["confidence"] = 0.5

        except Exception as e:
            # Fallback on any error
            self.logger.emit({"event": "openai_error", "error": str(e)}) if self.logger else None
            payload = {
                "decision": "NO",
                "rationale": f"Error evaluating: {str(e)}",
                "draft": "",
                "score": 0.0,
                "confidence": 0.0,
            }

        # Stamp versions to the payload for downstream use
        payload.setdefault("prompt_ver", self.prompt_ver)
        payload.setdefault("rubric_ver", self.rubric_ver)

        # Log usage if present
        self._log_usage(resp if "resp" in locals() else None)

        return dict(payload)
