"""Simple DI utilities to wire ports to use cases."""

from __future__ import annotations

from pathlib import Path

from ..application.gating import GatedDecision
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
    decision = LocalDecisionAdapter()
    template = template_text if template_text is not None else load_default_template()
    renderer = TemplateRenderer(template=template, banned_phrases=["guarantee", "promise"])
    gated = GatedDecision(scoring=scoring, decision=decision, message=renderer, threshold=threshold)
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

    quota = FileQuota()

    # Send use case needs a BrowserPort; will be wired later (semi-auto)
    class _NullBrowser:
        def focus_message_box(self) -> None: ...
        def fill_message(self, text: str) -> None: ...
        def send(self) -> None: ...

    send_use = SendMessage(quota=quota, browser=_NullBrowser(), logger=logger)

    return eval_use, send_use, logger
