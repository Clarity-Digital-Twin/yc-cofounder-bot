from __future__ import annotations

import os
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ..domain.entities import Criteria, Profile
from ..infrastructure.utils.normalize import hash_profile_text
from .ports import (
    BrowserPort,
    DecisionPort,
    LoggerPort,
    MessagePort,
    ProgressRepo,
    QuotaPort,
    SeenRepo,
    StopController,
)


@dataclass
class EvaluateProfile:
    decision: DecisionPort
    message: MessagePort

    def __call__(self, profile: Profile, criteria: Criteria) -> Mapping[str, Any]:
        data = self.decision.evaluate(profile, criteria)
        draft = self.message.render(data)
        return {**data, "draft": draft}


@dataclass
class SendMessage:
    quota: QuotaPort
    browser: BrowserPort
    logger: LoggerPort
    stop: StopController | None = None

    def __call__(self, draft: str, limit: int) -> bool:
        # Log send gate checks
        stop_is_set = self.stop and self.stop.is_stopped()
        quota_ok = self.quota.check_and_increment(limit) if not stop_is_set else False

        # Emit comprehensive gate event
        self.logger.emit(
            {
                "event": "send_gate",
                "stop": stop_is_set,
                "quota_ok": quota_ok,
                "draft_len": len(draft),
                "limit": limit,
            }
        )

        # Check stop flag at the very beginning
        if stop_is_set:
            self.logger.emit({"event": "stopped", "where": "send_message_start"})
            return False

        if not quota_ok:
            self.logger.emit({"event": "quota_block", "limit": limit})
            return False

        # Optional pacing delay between sends (seconds)
        try:
            pace_seconds = int(os.getenv("PACE_MIN_SECONDS", "45"))
        except Exception:
            pace_seconds = 45

        # Check stop before focus
        if self.stop and self.stop.is_stopped():
            self.logger.emit({"event": "stopped", "where": "before_focus"})
            return False

        self.browser.focus_message_box()

        # Check stop after focus, before fill
        if self.stop and self.stop.is_stopped():
            self.logger.emit({"event": "stopped", "where": "after_focus"})
            return False

        self.browser.fill_message(draft)

        # Check stop after fill, before send
        if self.stop and self.stop.is_stopped():
            self.logger.emit({"event": "stopped", "where": "before_send"})
            return False

        self.browser.send()

        # Optional pacing delay (check PACE_BLOCKING env var)
        pace_blocking = os.getenv("PACE_BLOCKING", "1") == "1"
        if pace_seconds and pace_blocking:
            time.sleep(pace_seconds)

        # Verify sent; retry once if needed
        if self.browser.verify_sent():
            self.logger.emit(
                {"event": "sent", "ok": True, "mode": "auto", "chars": len(draft), "verified": True}
            )
            return True
        # retry once
        self.logger.emit({"event": "verify_failed", "attempt": 1})

        # Check stop before retry
        if self.stop and self.stop.is_stopped():
            self.logger.emit({"event": "stopped", "where": "before_retry"})
            return False

        self.browser.send()

        # Apply pacing if blocking mode is enabled
        if pace_seconds and pace_blocking:
            time.sleep(pace_seconds)

        if self.browser.verify_sent():
            self.logger.emit(
                {
                    "event": "sent",
                    "ok": True,
                    "mode": "auto",
                    "chars": len(draft),
                    "verified": True,
                    "retry": 1,
                }
            )
            return True
        self.logger.emit({"event": "send_failed", "verified": False})
        return False


@dataclass
class ProcessCandidate:
    evaluate: EvaluateProfile
    send: SendMessage
    browser: BrowserPort
    seen: SeenRepo
    logger: LoggerPort
    progress: ProgressRepo | None = None
    stop: StopController | None = None

    def __call__(self, url: str, criteria: Criteria, limit: int, auto_send: bool = False) -> None:
        if self.stop is not None and self.stop.is_stopped():
            self.logger.emit({"event": "stopped"})
            return
        self.browser.open(url)
        if not self.browser.click_view_profile():
            self.logger.emit({"event": "no_profile"})
            return
        text = self.browser.read_profile_text()
        profile = Profile(raw_text=text)
        phash = hash_profile_text(text)
        if self.seen.is_seen(phash):
            self.logger.emit({"event": "skip_seen", "profile_hash": phash})
            self.browser.skip()
            return
        self.seen.mark_seen(phash)
        data = self.evaluate(profile, criteria)
        self.logger.emit({"event": "decision", "data": data})
        if self.stop is not None and self.stop.is_stopped():
            self.logger.emit({"event": "stopped"})
            return
        if auto_send and data.get("decision") == "YES":
            draft = str(data.get("draft", ""))
            if draft:
                sent = self.send(draft, limit)
                self.logger.emit({"event": "auto_send", "ok": sent})
        # update progress cursor last
        if self.progress is not None:
            self.progress.set_last(phash)
