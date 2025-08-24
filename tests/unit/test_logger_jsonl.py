import json
from pathlib import Path

from yc_matcher.infrastructure.logging.jsonl_logger import JSONLLogger


def test_jsonl_logger_writes_event(tmp_path: Path):
    p = tmp_path / "events.jsonl"
    log = JSONLLogger(p)
    log.emit({"event": "decision", "prompt_ver": "v1", "rubric_ver": "v1"})
    data = p.read_text(encoding="utf-8").strip().splitlines()
    assert len(data) == 1
    row = json.loads(data[0])
    assert row["event"] == "decision"
    assert row["prompt_ver"] == "v1"
    assert row["rubric_ver"] == "v1"
