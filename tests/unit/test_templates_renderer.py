from yc_matcher.infrastructure.templates import MAX_CHARS, TemplateRenderer


def test_template_renderer_slots_and_bans_and_clamps():
    tpl = "Hey [Name], about [project/skill] and [specific ability]. SECRET"
    r = TemplateRenderer(template=tpl, banned_phrases=["SECRET"])
    out = r.render({"extracted": {"name": "Sam"}})
    assert out.startswith("Hey Sam, about ")
    assert "SECRET" not in out

    # Clamp check
    long_tpl = "x" * (MAX_CHARS + 50)
    r2 = TemplateRenderer(template=long_tpl)
    out2 = r2.render({"extracted": {"name": "Sam"}})
    assert len(out2) == MAX_CHARS
