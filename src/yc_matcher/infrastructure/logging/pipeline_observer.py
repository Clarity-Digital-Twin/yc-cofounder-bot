"""
Professional send pipeline observability layer.
Implements the 10-event trace pattern to diagnose send failures.
"""

import hashlib
from typing import Any
from uuid import uuid4

from .time_utils import utc_isoformat


class SendPipelineObserver:
    """Trace every step of the send pipeline with deterministic events."""

    def __init__(self, logger: Any) -> None:
        self.logger = logger
        self.run_id = str(uuid4())[:8]  # Short run ID
        self.profile_seq = 0

    def new_profile(self) -> int:
        """Start tracking a new profile."""
        self.profile_seq += 1
        return self.profile_seq

    def _emit(self, event: str, data: dict[str, Any]) -> None:
        """Emit event with run_id and profile_seq."""
        self.logger.emit(
            {
                "event": event,
                "run_id": self.run_id,
                "profile_seq": self.profile_seq,
                "timestamp": utc_isoformat(),
                **data,
            }
        )

    # 1. Profile extraction
    def profile_extracted(self, text: str) -> None:
        """Log profile extraction."""
        self._emit(
            "profile_extracted",
            {"extracted_len": len(text), "hash": hashlib.md5(text.encode()).hexdigest()[:8]},
        )

    # 2. Decision request
    def decision_request(self, model: str, input_text: str) -> None:
        """Log decision request."""
        self._emit("decision_request", {"model": model, "input_len": len(input_text)})

    # 3. Decision response
    def decision_response(
        self,
        decision: str,
        auto_send: bool,
        output_types: list[str],
        latency_ms: int,
        decision_json_ok: bool = True,
    ) -> None:
        """Log decision response."""
        self._emit(
            "decision_response",
            {
                "decision": decision,
                "auto_send": auto_send,
                "decision_json_ok": decision_json_ok,
                "output_types": output_types,
                "latency_ms": latency_ms,
            },
        )

    # 4. Send gate checks
    def send_gate(
        self,
        stop: bool,
        quota_ok: bool,
        seen_ok: bool,
        mode: str,
        auto_send: bool,
        remaining_quota: int = 0,
    ) -> None:
        """Log all gate checks before send."""
        self._emit(
            "send_gate",
            {
                "stop": stop,
                "quota_ok": quota_ok,
                "seen_ok": seen_ok,
                "mode": mode,
                "auto_send": auto_send,
                "remaining_quota": remaining_quota,
            },
        )

    # 5. Focus message box
    def focus_message_box_result(
        self, ok: bool, selector_used: str | None = None, error: str | None = None
    ) -> None:
        """Log focus attempt result."""
        self._emit(
            "focus_message_box_result", {"ok": ok, "selector_used": selector_used, "error": error}
        )

    # 6. Fill message
    def fill_message_result(
        self, ok: bool, chars: int, selector_used: str | None = None, error: str | None = None
    ) -> None:
        """Log fill attempt result."""
        self._emit(
            "fill_message_result",
            {"ok": ok, "chars": chars, "selector_used": selector_used, "error": error},
        )

    # 7. Click send
    def click_send_result(
        self, ok: bool, button_variant: str | None = None, error: str | None = None
    ) -> None:
        """Log send button click result."""
        self._emit(
            "click_send_result", {"ok": ok, "button_variant": button_variant, "error": error}
        )

    # 8. Verify sent attempt
    def verify_sent_attempt(self, checks_tried: list[str]) -> None:
        """Log verification checks attempted."""
        self._emit("verify_sent_attempt", {"checks_tried": checks_tried})

    # 9. Verify sent result
    def verify_sent_result(
        self, ok: bool, matched_selector: str | None = None, counts: dict[str, Any] | None = None
    ) -> None:
        """Log verification result."""
        self._emit(
            "verify_sent_result",
            {"ok": ok, "matched_selector": matched_selector, "counts": counts or {}},
        )

    # 10. Final sent event
    def sent(self) -> None:
        """Log successful send (only if verify was ok)."""
        self._emit("sent", {"success": True})
