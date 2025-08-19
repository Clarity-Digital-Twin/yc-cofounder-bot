from pathlib import Path
import json
from yc_matcher.infrastructure.jsonl_logger import JSONLLogger
from yc_matcher.infrastructure.logger_stamped import LoggerWithStamps


def test_logger_stamps_versions_and_preset(tmp_path: Path):
    p = tmp_path / "events.jsonl"
    base = JSONLLogger(p)
    log = LoggerWithStamps(base, prompt_ver="v1", rubric_ver="v1", criteria_preset="NYC-AI")
    log.emit({"event": "decision"})
    row = json.loads(p.read_text(encoding="utf-8").strip())
    assert row["event"] == "decision"
    assert row["prompt_ver"] == "v1"
    assert row["rubric_ver"] == "v1"
    assert row["criteria_preset"] == "NYC-AI"

