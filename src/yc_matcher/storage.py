from __future__ import annotations

import json
from pathlib import Path


DEFAULT_COUNTER = Path("sent_counter.json")


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_count(path: Path = DEFAULT_COUNTER) -> int:
    data = _read_json(path)
    return int(data.get("count", 0))


def write_count(n: int, path: Path = DEFAULT_COUNTER) -> None:
    path.write_text(json.dumps({"count": int(n)}), encoding="utf-8")


def reset_count(path: Path = DEFAULT_COUNTER) -> None:
    write_count(0, path)
