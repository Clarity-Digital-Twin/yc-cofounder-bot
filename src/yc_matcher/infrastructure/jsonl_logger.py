from __future__ import annotations

import json
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class JSONLLogger:
    def __init__(self, path: Path) -> None:
        self.path = path

    def emit(self, event: Mapping[str, Any]) -> None:
        row = {"ts": time.time(), **event}
        line = json.dumps(row, ensure_ascii=False)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
