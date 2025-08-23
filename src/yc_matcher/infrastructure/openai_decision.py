from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .. import config
from ..application.ports import DecisionPort, LoggerPort
from ..domain.entities import Criteria, Profile
from .error_recovery import RetryWithBackoff


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

        # Setup retry mechanism for API resilience
        retry = RetryWithBackoff(
            max_retries=3,
            initial_delay=2.0,
            logger=self.logger,
        )

        # Track latency
        import time

        decision_start = time.time()

        # Use the correct OpenAI chat completions API
        try:
            # Define API call functions for retry wrapper
            def call_gpt5() -> tuple[Any, str]:
                # Try with response_format first (per feedback this may be supported now)
                # Fall back to prompt-based JSON if it fails
                try:
                    r = self.client.responses.create(
                        model=self.model,
                        input=[
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": user_text},
                        ],
                        response_format={
                            "type": "json_schema",
                            "json_schema": {
                                "name": "decision_response",
                                "strict": True,
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "decision": {"type": "string", "enum": ["YES", "NO"]},
                                        "rationale": {"type": "string"},
                                        "draft": {"type": "string"},
                                        "score": {"type": "number", "minimum": 0, "maximum": 1},
                                        "confidence": {
                                            "type": "number",
                                            "minimum": 0,
                                            "maximum": 1,
                                        },
                                    },
                                    "required": [
                                        "decision",
                                        "rationale",
                                        "draft",
                                        "score",
                                        "confidence",
                                    ],
                                    "additionalProperties": False,
                                },
                            },
                        },
                        max_output_tokens=800,  # Responses API uses max_output_tokens
                        temperature=0.3,  # Stable for structured outputs (0.2-0.5 recommended)
                    )
                except Exception as format_err:
                    # Fallback: instruct JSON format in the prompt
                    if self.logger:
                        self.logger.emit(
                            {
                                "event": "response_format_fallback",
                                "error": str(format_err),
                                "model": self.model,
                            }
                        )
                    r = self.client.responses.create(
                        model=self.model,
                        input=[
                            {"role": "system", "content": sys_prompt},
                            {
                                "role": "user",
                                "content": user_text
                                + "\n\nIMPORTANT: Return your response as valid JSON.",
                            },
                        ],
                        max_output_tokens=800,  # Responses API uses max_output_tokens
                        temperature=0.3,  # Stable for structured outputs (0.2-0.5 recommended)
                    )
                # Extract content from Responses API format
                # GPT-5 returns output array: [reasoning_item, message_item]
                # Use output_text helper which aggregates all text (docs-recommended)
                c = None

                # First try the SDK's output_text helper (fastest, most reliable)
                if hasattr(r, "output_text"):
                    c = r.output_text
                    if self.logger:
                        try:
                            text_len = len(c) if c else 0
                        except (TypeError, AttributeError):
                            # Handle mocks in tests
                            text_len = 0
                        self.logger.emit(
                            {
                                "event": "gpt5_parse_method",
                                "method": "output_text",
                                "text_len": text_len,
                            }
                        )

                # Fallback to manual parsing if output_text not available
                elif hasattr(r, "output") and isinstance(r.output, list):
                    text_parts = []
                    output_types = []

                    for item in r.output:
                        item_type = getattr(item, "type", "unknown")
                        output_types.append(item_type)

                        # Skip reasoning items (only log them)
                        if item_type == "reasoning":
                            if self.logger:
                                self.logger.emit(
                                    {
                                        "event": "gpt5_reasoning_item",
                                        "content": str(getattr(item, "content", ""))[:200],
                                    }
                                )
                            continue

                        # Process message items
                        if item_type == "message":
                            if hasattr(item, "content"):
                                # Handle both list and direct text content
                                if isinstance(item.content, list):
                                    for content_item in item.content:
                                        if hasattr(content_item, "text"):
                                            text_parts.append(content_item.text)
                                        elif (
                                            hasattr(content_item, "type")
                                            and content_item.type == "output_text"
                                        ):
                                            # Some SDKs use output_text type in content
                                            text_parts.append(getattr(content_item, "text", ""))
                                elif isinstance(item.content, str):
                                    text_parts.append(item.content)

                    c = "".join(text_parts)

                    if self.logger:
                        try:
                            text_len = len(c) if c else 0
                        except (TypeError, AttributeError):
                            # Handle mocks in tests
                            text_len = 0
                        self.logger.emit(
                            {
                                "event": "gpt5_parse_method",
                                "method": "manual_iteration",
                                "output_types": output_types,
                                "text_len": text_len,
                            }
                        )

                if not c:
                    # Log detailed error for debugging
                    error_detail = {
                        "event": "gpt5_parse_failure",
                        "has_output": hasattr(r, "output"),
                        "has_output_text": hasattr(r, "output_text"),
                        "output_items": len(r.output) if hasattr(r, "output") and r.output else 0,
                        "output_types": [getattr(item, "type", "unknown") for item in r.output]
                        if hasattr(r, "output") and r.output
                        else [],
                    }
                    if self.logger:
                        self.logger.emit(error_detail)

                    raise ValueError(
                        f"Could not extract text from GPT-5 response. "
                        f"Output items: {error_detail['output_items']}, "
                        f"Types: {error_detail['output_types']}"
                    )

                return r, c

            def call_gpt4() -> tuple[Any, str]:
                # Fallback to Chat Completions for GPT-4 and older
                r = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_text},
                    ],
                    response_format={"type": "json_object"},  # Force JSON response
                    temperature=0.3,  # Stable for structured outputs (0.2-0.5 recommended)
                    max_tokens=800,  # Enough for decision + message
                )
                # Parse the JSON response
                c = r.choices[0].message.content
                return r, c

            # Use Responses API for GPT-5, Chat Completions for GPT-4
            if self.model.startswith("gpt-5"):
                resp, content = retry.execute(
                    call_gpt5,
                    operation_name=f"gpt5_decision_{self.model}",
                    retryable_exceptions=(Exception,),
                )
            else:
                resp, content = retry.execute(
                    call_gpt4,
                    operation_name=f"gpt4_decision_{self.model}",
                    retryable_exceptions=(Exception,),
                )
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
            # Log detailed error for debugging
            error_detail = {
                "event": "openai_error",
                "error": str(e),
                "error_type": type(e).__name__,
                "model": self.model,
                "profile_length": len(profile.raw_text),
                "criteria_length": len(criteria.text),
            }
            self.logger.emit(error_detail) if self.logger else None

            # Return ERROR decision (not NO) to distinguish from real rejections
            payload = {
                "decision": "ERROR",
                "rationale": f"OpenAI API Error ({type(e).__name__}): {str(e)[:200]}",
                "draft": "",
                "score": 0.0,
                "confidence": 0.0,
                "error": str(e),
                "error_type": type(e).__name__,
            }

        # Add latency to payload
        decision_ms = int((time.time() - decision_start) * 1000)
        payload["latency_ms"] = decision_ms

        # Stamp versions to the payload for downstream use
        payload.setdefault("prompt_ver", self.prompt_ver)
        payload.setdefault("rubric_ver", self.rubric_ver)

        # Log usage if present (with latency)
        if self.logger and "resp" in locals():
            self._log_usage(resp)
            self.logger.emit(
                {
                    "event": "decision_latency",
                    "model": self.model,
                    "latency_ms": decision_ms,
                    "success": payload.get("decision") != "ERROR",
                }
            )

        return dict(payload)
