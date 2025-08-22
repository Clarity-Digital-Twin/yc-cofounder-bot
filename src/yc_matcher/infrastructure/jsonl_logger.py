from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class JSONLLogger:
    def __init__(self, path: Path) -> None:
        self.path = path

    def emit(self, event: Mapping[str, Any]) -> None:
        # Always emit both ts (Unix) and timestamp (ISO) for compatibility
        now = datetime.now(UTC)
        row = {
            "ts": now.timestamp(),
            "timestamp": now.isoformat(),
            **event
        }
        line = json.dumps(row, ensure_ascii=False)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
