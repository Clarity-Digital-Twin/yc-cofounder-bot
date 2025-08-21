"""Simple DI utilities to wire ports to use cases."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

from ..application.gating import GatedDecision
from ..application.ports import BrowserPort, DecisionPort, ScoringPort
from ..application.use_cases import EvaluateProfile, SendMessage
from ..domain.services import WeightedScoringService
from ..infrastructure.jsonl_logger import JSONLLogger
from ..infrastructure.local_decision import LocalDecisionAdapter
from ..infrastructure.logger_stamped import LoggerWithStamps
from ..infrastructure.quota import FileQuota
from ..infrastructure.sqlite_quota import SQLiteDailyWeeklyQuota
from ..infrastructure.stop_flag import FileStopFlag
from ..infrastructure.template_loader import load_default_template
from ..infrastructure.templates import TemplateRenderer


class RubricOnlyAdapter(DecisionPort):
    """Pure rubric-based decision adapter (Strategy Pattern).

    SOLID: Single Responsibility - Only handles rubric scoring
    DRY: Reuses WeightedScoringService
    """

    def __init__(self, scoring: ScoringPort, threshold: float = 4.0) -> None:
        self.scoring = scoring
        self.threshold = threshold
        self.auto_send = True  # Rubric mode always auto-sends if threshold met

    def evaluate(self, profile: Any, criteria: Any) -> dict[str, Any]:
        """Evaluate using pure scoring rules."""
        score = self.scoring.score(profile, criteria)
        passed = score.value >= self.threshold

        return {
            "decision": "YES" if passed else "NO",
            "rationale": f"Rubric score: {score.value:.1f} (threshold: {self.threshold})",
            "draft": "" if not passed else "Message would be generated here",
            "mode": "rubric",
            "auto_send": self.auto_send and passed,
            "score": score.value,
            "threshold": self.threshold,
        }


def create_decision_adapter(
    mode: str | None = None,
    scoring: ScoringPort | None = None,
    threshold: float = 4.0,
    client: Any = None,
    logger: Any = None,
    prompt_ver: str = "v1",
    rubric_ver: str = "v1",
) -> DecisionPort:
    """Factory method for decision adapters (Factory Pattern).

    Strategy Pattern: Different decision strategies based on mode
    Open/Closed: Easy to add new modes without modifying existing
    """
    mode = mode or os.getenv("DECISION_MODE", "hybrid")

    # Create base decision adapter (AI-based)
    ai_decision: DecisionPort = LocalDecisionAdapter()
    if os.getenv("ENABLE_OPENAI", "0") in {"1", "true", "True"}:
        try:
            from ..infrastructure.openai_decision import OpenAIDecisionAdapter

            if client is None:
                try:
                    from openai import OpenAI

                    client = OpenAI()
                except Exception:
                    # Fallback client
                    class _Noop:
                        class responses:
                            @staticmethod
                            def create(**_: Any) -> Any:
                                return type(
                                    "R",
                                    (),
                                    {
                                        "output": {
                                            "decision": "NO",
                                            "rationale": "offline",
                                            "draft": "",
                                        }
                                    },
                                )()

                    client = _Noop()

            ai_decision = OpenAIDecisionAdapter(
                client=client, logger=logger, prompt_ver=prompt_ver, rubric_ver=rubric_ver
            )
        except Exception:
            pass  # Keep LocalDecisionAdapter

    # Mode-specific adapter creation
    if mode == "advisor":
        # Pure AI, no auto-send
        if hasattr(ai_decision, "auto_send"):
            ai_decision.auto_send = False
        return ai_decision

    elif mode == "rubric":
        # Pure scoring, always auto-send if threshold met
        if scoring is None:
            raise ValueError("Rubric mode requires scoring service")
        return RubricOnlyAdapter(scoring=scoring, threshold=threshold)

    elif mode == "hybrid":
        # Combined: scoring gate + AI decision
        if scoring is None:
            raise ValueError("Hybrid mode requires scoring service")

        # Use environment variables for hybrid configuration
        hybrid_threshold = float(os.getenv("HYBRID_THRESHOLD", str(threshold)))

        return GatedDecision(scoring=scoring, decision=ai_decision, threshold=hybrid_threshold)

    else:
        raise ValueError(f"Unknown decision mode: {mode}")


def build_services(
    *,
    criteria_text: str,
    template_text: str | None = None,
    prompt_ver: str = "v1",
    rubric_ver: str = "v1",
    criteria_preset: str | None = None,
    weights: dict[str, float] | None = None,
    threshold: float = 4.0,
    decision_mode: str | None = None,
) -> tuple[EvaluateProfile, SendMessage, LoggerWithStamps]:
    # Scoring
    default_weights = {"python": 3.0, "fastapi": 2.0, "health": 2.0, "ny": 1.0, "crypto": -999.0}
    _w = weights or default_weights
    weights_float = {k: float(v) for k, v in _w.items()}
    scoring = WeightedScoringService(weights_float)

    # Template rendering
    template = template_text if template_text is not None else load_default_template()
    renderer = TemplateRenderer(template=template, banned_phrases=["guarantee", "promise"])

    # Create decision adapter based on mode (Strategy Pattern)
    # Logger is created below, so pass None for now
    decision = create_decision_adapter(
        mode=decision_mode,
        scoring=scoring,
        threshold=threshold,
        client=None,  # Will be created inside if needed
        logger=None,  # Will be attached below
        prompt_ver=prompt_ver,
        rubric_ver=rubric_ver,
    )

    eval_use = EvaluateProfile(decision=decision, message=renderer)

    # Logger and quota/seen
    logs_path = Path(".runs") / "events.jsonl"
    base_logger = JSONLLogger(logs_path)
    logger = LoggerWithStamps(
        base_logger,
        prompt_ver=prompt_ver,
        rubric_ver=rubric_ver,
        criteria_preset=criteria_preset or "custom",
    )
    # Attach logger to decision adapter if it supports it
    if hasattr(decision, "logger") and decision.logger is None:
        decision.logger = logger
    # For GatedDecision, attach to inner decision
    if isinstance(decision, GatedDecision) and hasattr(decision.decision, "logger"):
        if decision.decision.logger is None:
            decision.decision.logger = logger

    # Quota: calendar-aware (daily/weekly) if enabled, else simple file counter
    quota = (
        SQLiteDailyWeeklyQuota(Path(".runs/quota.sqlite"))
        if os.getenv("ENABLE_CALENDAR_QUOTA", "0") in {"1", "true", "True"}
        else FileQuota()
    )

    # Send use case needs a BrowserPort; CUA primary, Playwright fallback
    class _NullBrowser:
        def focus_message_box(self) -> None: ...
        def fill_message(self, text: str) -> None: ...
        def send(self) -> None: ...
        def verify_sent(self) -> bool:
            return True

        def open(self, url: str) -> None: ...
        def click_view_profile(self) -> bool:
            return True

        def read_profile_text(self) -> str:
            return ""

        def skip(self) -> None: ...
        def close(self) -> None: ...

    browser: BrowserPort

    # PRIMARY: OpenAI CUA via Responses API (FIXED with AsyncLoopRunner)
    if os.getenv("ENABLE_CUA", "0") in {"1", "true", "True"}:
        try:
            from ..infrastructure.openai_cua_browser import OpenAICUABrowser

            browser = cast(BrowserPort, OpenAICUABrowser())
        except Exception:
            # Fallback to Playwright if CUA fails
            if os.getenv("ENABLE_PLAYWRIGHT_FALLBACK", "0") in {"1", "true", "True"}:
                from ..infrastructure.browser_playwright import PlaywrightBrowser

                browser = cast(BrowserPort, PlaywrightBrowser())
            else:
                browser = cast(BrowserPort, _NullBrowser())
    # FALLBACK: Playwright when CUA not enabled
    elif os.getenv("ENABLE_PLAYWRIGHT", "0") in {"1", "true", "True"}:
        from ..infrastructure.browser_playwright import PlaywrightBrowser

        browser = cast(BrowserPort, PlaywrightBrowser())
    else:
        browser = cast(BrowserPort, _NullBrowser())

    # Create stop controller (shared between ProcessCandidate and SendMessage)
    stop = FileStopFlag(Path(".runs/stop.flag"))

    send_use = SendMessage(quota=quota, browser=browser, logger=logger, stop=stop)

    return eval_use, send_use, logger
