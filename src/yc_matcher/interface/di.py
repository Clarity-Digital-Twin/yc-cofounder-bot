"""Simple DI utilities to wire ports to use cases."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

from ..application.gating import GatedDecision
from ..application.ports import BrowserPort, DecisionPort
from ..application.use_cases import EvaluateProfile, SendMessage
from ..domain.services import WeightedScoringService
from ..infrastructure.jsonl_logger import JSONLLogger
from ..infrastructure.local_decision import LocalDecisionAdapter
from ..infrastructure.logger_stamped import LoggerWithStamps
from ..infrastructure.quota import FileQuota
from ..infrastructure.template_loader import load_default_template
from ..infrastructure.templates import TemplateRenderer


def build_services(
    *,
    criteria_text: str,
    template_text: str | None = None,
    prompt_ver: str = "v1",
    rubric_ver: str = "v1",
    criteria_preset: str | None = None,
    weights: dict[str, float] | None = None,
    threshold: float = 4.0,
) -> tuple[EvaluateProfile, SendMessage, LoggerWithStamps]:
    # Scoring
    default_weights = {"python": 3.0, "fastapi": 2.0, "health": 2.0, "ny": 1.0, "crypto": -999.0}
    _w = weights or default_weights
    weights_float = {k: float(v) for k, v in _w.items()}
    scoring = WeightedScoringService(weights_float)

    # Decision + message rendering
    decision: DecisionPort = LocalDecisionAdapter()
    template = template_text if template_text is not None else load_default_template()
    renderer = TemplateRenderer(template=template, banned_phrases=["guarantee", "promise"])
    # Optionally replace decision with OpenAI adapter if enabled
    if os.getenv("ENABLE_OPENAI", "0") in {"1", "true", "True"}:
        try:
            from ..infrastructure.openai_decision import OpenAIDecisionAdapter
            # Lazy import of SDK done inside adapter by client you pass. Here we assume a client will be created by consumer;
            # For now, use a very lightweight placeholder that matches our FakeClient in tests if real client missing.
            try:
                from openai import OpenAI
                client: Any = OpenAI()
            except Exception:
                class _Noop:
                    class responses:
                        @staticmethod
                        def create(**_: Any) -> Any:
                            return type("R", (), {"output": {"decision": "NO", "rationale": "offline", "draft": ""}})()
                client = _Noop()
            # logger is defined below; create a temporary base for decision stamping
            decision = OpenAIDecisionAdapter(client=client, logger=None, prompt_ver=prompt_ver, rubric_ver=rubric_ver)
        except Exception:
            # Fallback to local decision if adapter import fails
            decision = LocalDecisionAdapter()
    gated: DecisionPort = GatedDecision(scoring=scoring, decision=decision, threshold=threshold)
    eval_use = EvaluateProfile(decision=gated, message=renderer)

    # Logger and quota/seen
    logs_path = Path(".runs") / "events.jsonl"
    base_logger = JSONLLogger(logs_path)
    logger = LoggerWithStamps(
        base_logger,
        prompt_ver=prompt_ver,
        rubric_ver=rubric_ver,
        criteria_preset=criteria_preset or "custom",
    )
    # If decision adapter exists without logger, attach the stamped logger now
    try:
        from ..infrastructure.openai_decision import OpenAIDecisionAdapter
        if isinstance(decision, OpenAIDecisionAdapter) and decision.logger is None:
            decision.logger = logger
    except Exception:
        pass

    quota = FileQuota()

    # Send use case needs a BrowserPort; allow Playwright behind a flag
    class _NullBrowser:
        def focus_message_box(self) -> None: ...
        def fill_message(self, text: str) -> None: ...
        def send(self) -> None: ...
        def verify_sent(self) -> bool: return True
        def open(self, url: str) -> None: ...
        def click_view_profile(self) -> bool: return True
        def read_profile_text(self) -> str: return ""
        def skip(self) -> None: ...
        def close(self) -> None: ...

    browser: BrowserPort
    if os.getenv("ENABLE_PLAYWRIGHT", "0") in {"1", "true", "True"}:
        # Import lazily to avoid mypy/import issues when playwright is unavailable
        from ..infrastructure.browser_playwright import PlaywrightBrowser
        browser = cast(BrowserPort, PlaywrightBrowser())
    else:
        browser = cast(BrowserPort, _NullBrowser())

    send_use = SendMessage(quota=quota, browser=browser, logger=logger)

    return eval_use, send_use, logger
