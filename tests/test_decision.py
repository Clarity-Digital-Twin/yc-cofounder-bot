from yc_matcher.decision import decide_and_draft


def test_decision_yes_with_keyword_match():
    criteria = "python, fastapi"
    profile = "Jane Doe\n... experienced with Python and FastAPI ..."
    template = "Hey [Name], your [project/skill] shows [specific ability]."
    r = decide_and_draft(criteria, profile, template)
    assert r.decision == "YES"
    assert "match" in r.rationale.lower() or "fit" in r.rationale.lower()
    assert "Hey Jane" in r.message


def test_decision_no_when_no_keywords():
    criteria = "rust, embedded"
    profile = "Alex Smith\n... experienced with Python and data science ..."
    template = "Hey [Name], your [project/skill] shows [specific ability]."
    r = decide_and_draft(criteria, profile, template)
    assert r.decision == "NO"
    assert r.message == ""
