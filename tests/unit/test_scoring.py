from yc_matcher.domain.entities import Criteria, Profile
from yc_matcher.domain.services import ScoringService, WeightedScoringService


def test_basic_keyword_scoring_counts_hits():
    s = ScoringService()
    p = Profile(raw_text="Expert in Python, FastAPI, and healthcare")
    c = Criteria(text="python,fastapi,react")
    score = s.score(p, c)
    assert score.value == 2
    assert "keyword:python" in score.reasons


def test_weighted_scoring_with_threshold_and_red_flag():
    svc = WeightedScoringService(
        weights={"python": 3, "fastapi": 2, "health": 2, "ny": 1, "crypto": -999}
    )
    p = Profile(raw_text="Python + FastAPI in health, NYC")
    c = Criteria(text="python, fastapi, health, ny")
    score = svc.score(p, c)
    assert score.value >= 7  # 3+2+2

    # Red flag forces very negative
    p2 = Profile(raw_text="Senior Python dev, crypto projects")
    score2 = svc.score(p2, c)
    assert score2.value < -100
