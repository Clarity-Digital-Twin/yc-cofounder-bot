from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from yc_matcher.application.ports import LoggerPort


class LoggerWithStamps(LoggerPort):
    def __init__(
        self,
        logger: LoggerPort,
        prompt_ver: str,
        rubric_ver: str,
        criteria_preset: str | None = None,
    ) -> None:
        self._logger = logger
        self._prompt_ver = prompt_ver
        self._rubric_ver = rubric_ver
        self._criteria_preset = criteria_preset or "custom"

    def emit(self, event: Mapping[str, Any]) -> None:
        stamped = {
            "prompt_ver": self._prompt_ver,
            "rubric_ver": self._rubric_ver,
            "criteria_preset": self._criteria_preset,
            **event,
        }
        self._logger.emit(stamped)

    @property
    def prompt_ver(self) -> str:
        return self._prompt_ver

    @property
    def rubric_ver(self) -> str:
        return self._rubric_ver

    @property
    def criteria_preset(self) -> str:
        return self._criteria_preset
