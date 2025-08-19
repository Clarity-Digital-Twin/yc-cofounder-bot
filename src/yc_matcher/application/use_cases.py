from __future__ import annotations

import os
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ..domain.entities import Criteria, Profile
from ..infrastructure.normalize import hash_profile_text
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

    def __call__(self, draft: str, limit: int) -> bool:
        if not self.quota.check_and_increment(limit):
            self.logger.emit({"event": "quota_block", "limit": limit})
            return False
        # Optional pacing delay between sends (ms)
        try:
            delay_ms = int(os.getenv("SEND_DELAY_MS", "0"))
        except Exception:
            delay_ms = 0
        self.browser.focus_message_box()
        self.browser.fill_message(draft)
        self.browser.send()
        if delay_ms:
            time.sleep(delay_ms / 1000.0)
        # Verify sent; retry once if needed
        if self.browser.verify_sent():
            self.logger.emit({"event": "sent", "ok": True, "mode": "auto", "chars": len(draft), "verified": True})
            return True
        # retry once
        self.logger.emit({"event": "verify_failed", "attempt": 1})
        self.browser.send()
        if delay_ms:
            time.sleep(delay_ms / 1000.0)
        if self.browser.verify_sent():
            self.logger.emit({"event": "sent", "ok": True, "mode": "auto", "chars": len(draft), "verified": True, "retry": 1})
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
