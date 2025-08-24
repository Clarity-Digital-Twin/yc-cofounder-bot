"""Simple DI utilities to wire ports to use cases."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from .. import config
from ..application.ports import BrowserPort, DecisionPort
from ..application.use_cases import EvaluateProfile, SendMessage
from ..infrastructure.logging.jsonl_logger import JSONLLogger
from ..infrastructure.ai.local_decision import LocalDecisionAdapter
from ..infrastructure.logging.stamped_logger import LoggerWithStamps
from ..infrastructure.ai.model_resolver import resolve_and_set_models
from ..infrastructure.control.quota import FileQuota
from ..infrastructure.persistence.sqlite_quota import SQLiteDailyWeeklyQuota
from ..infrastructure.control.stop_flag import FileStopFlag
from ..infrastructure.utils.template_loader import load_default_template
from ..infrastructure.utils.templates import TemplateRenderer


def build_services(
    *,
    criteria_text: str,
    template_text: str | None = None,
    prompt_ver: str = "v1",
    rubric_ver: str = "v1",
    criteria_preset: str | None = None,
    enable_cua: bool | None = None,  # Override CUA setting from UI
) -> tuple[EvaluateProfile, SendMessage, LoggerWithStamps]:
    # Resolve models at startup (once per session)
    # This sets DECISION_MODEL_RESOLVED and CUA_MODEL_RESOLVED env vars
    if not config.get_decision_model().startswith("gpt"):
        try:
            resolve_and_set_models()
        except Exception as e:
            print(f"⚠️ Model resolution failed: {e}")
            # Continue with fallback to env vars

    # Template rendering
    template = template_text if template_text is not None else load_default_template()
    renderer = TemplateRenderer(template=template, banned_phrases=["guarantee", "promise"])

    # Create decision adapter
    decision: DecisionPort = LocalDecisionAdapter()  # Default fallback
    if config.is_openai_enabled():
        try:
            from openai import OpenAI

            from ..infrastructure.openai_decision import OpenAIDecisionAdapter

            client = OpenAI()
            decision = OpenAIDecisionAdapter(
                client=client,
                logger=None,  # Will be attached below
                model=config.get_decision_model(),
                prompt_ver=prompt_ver,
                rubric_ver=rubric_ver,
            )
        except Exception as e:
            print(f"⚠️ OpenAI initialization failed: {e}, using local fallback")
            # Keep LocalDecisionAdapter as fallback

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

    # Quota: calendar-aware (daily/weekly) if enabled, else simple file counter
    quota = (
        SQLiteDailyWeeklyQuota(Path(".runs/quota.sqlite"))
        if config.is_calendar_quota_enabled()
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
    # Use UI toggle if provided, otherwise fall back to config
    use_cua = enable_cua if enable_cua is not None else config.is_cua_enabled()
    if use_cua:
        try:
            from ..infrastructure.openai_cua_browser import OpenAICUABrowser

            browser = cast(BrowserPort, OpenAICUABrowser())
        except Exception:
            # Fallback to Playwright if CUA fails
            if config.get_playwright_fallback_enabled():
                # Use async-compatible version to avoid "Sync API in asyncio loop" error
                from ..infrastructure.browser_playwright_async import PlaywrightBrowserAsync

                browser = cast(BrowserPort, PlaywrightBrowserAsync())
            else:
                browser = cast(BrowserPort, _NullBrowser())
    # FALLBACK: Playwright when CUA not enabled
    elif config.is_playwright_enabled():
        # Use async-compatible version to avoid "Sync API in asyncio loop" error
        from ..infrastructure.browser_playwright_async import PlaywrightBrowserAsync

        browser = cast(BrowserPort, PlaywrightBrowserAsync())
    else:
        browser = cast(BrowserPort, _NullBrowser())

    # Create stop controller (shared between ProcessCandidate and SendMessage)
    stop = FileStopFlag(Path(".runs/stop.flag"))

    send_use = SendMessage(quota=quota, browser=browser, logger=logger, stop=stop)

    return eval_use, send_use, logger
