from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ..domain.entities import Criteria, Profile
from .ports import BrowserPort, DecisionPort, LoggerPort, MessagePort, QuotaPort, SeenRepo


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
        self.browser.focus_message_box()
        self.browser.fill_message(draft)
        self.browser.send()
        self.logger.emit({"event": "sent", "chars": len(draft)})
        return True


@dataclass
class ProcessCandidate:
    evaluate: EvaluateProfile
    send: SendMessage
    browser: BrowserPort
    seen: SeenRepo
    logger: LoggerPort

    def __call__(self, url: str, criteria: Criteria, limit: int) -> None:
        self.browser.open(url)
        if not self.browser.click_view_profile():
            self.logger.emit({"event": "no_profile"})
            return
        text = self.browser.read_profile_text()
        profile = Profile(raw_text=text)
        phash = str(abs(hash(text)))
        if self.seen.is_seen(phash):
            self.logger.emit({"event": "skip_seen", "profile_hash": phash})
            self.browser.skip()
            return
        data = self.evaluate(profile, criteria)
        # Decision gate is HIL-controlled in UI; here we just log
        self.logger.emit({"event": "decision", "data": data})
