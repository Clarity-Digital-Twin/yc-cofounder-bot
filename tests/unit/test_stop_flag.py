from pathlib import Path

from yc_matcher.infrastructure.control.stop_flag import FileStopFlag


def test_file_stop_flag_roundtrip(tmp_path: Path):
    p = tmp_path / "stop.flag"
    f = FileStopFlag(p)
    assert f.is_stopped() is False
    f.set()
    assert f.is_stopped() is True
    f.clear()
    assert f.is_stopped() is False
