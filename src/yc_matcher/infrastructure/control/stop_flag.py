from __future__ import annotations

from pathlib import Path

from yc_matcher.application.ports import StopController


class FileStopFlag(StopController):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def is_stopped(self) -> bool:
        return self.path.exists()

    def set(self) -> None:
        self.path.write_text("stop", encoding="utf-8")

    def clear(self) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
