from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from ..domain.entities import Criteria, Profile, Score


class DecisionPort(Protocol):
    def evaluate(self, profile: Profile, criteria: Criteria) -> Mapping[str, Any]:
        """Return structured decision JSON (already schema-validated upstream/downstream)."""


class MessagePort(Protocol):
    def render(self, decision: Mapping[str, Any]) -> str:
        """Render a message from decision + template, applying clamps/safety."""


class ScoringPort(Protocol):
    def score(self, profile: Profile, criteria: Criteria) -> Score: ...


class QuotaPort(Protocol):
    def check_and_increment(self, limit: int) -> bool:  # True if another send allowed
        ...


class SeenRepo(Protocol):
    def is_seen(self, profile_hash: str) -> bool: ...

    def mark_seen(self, profile_hash: str) -> None: ...


class LoggerPort(Protocol):
    def emit(self, event: Mapping[str, Any]) -> None: ...


class BrowserPort(Protocol):
    def open(self, url: str) -> None: ...

    def click_view_profile(self) -> bool: ...

    def read_profile_text(self) -> str: ...

    def focus_message_box(self) -> None: ...

    def fill_message(self, text: str) -> None: ...

    def send(self) -> None: ...

    def skip(self) -> None: ...
