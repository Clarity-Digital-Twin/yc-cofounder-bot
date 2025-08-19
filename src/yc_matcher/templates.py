from __future__ import annotations

from pathlib import Path


DEFAULT_TEMPLATE_PATHS = [
    Path("MATCH_MESSAGE_TEMPLATE.MD"),
    Path("docs/MATCH_MESSAGE_TEMPLATE.MD"),
]


def load_default_template() -> str:
    for p in DEFAULT_TEMPLATE_PATHS:
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
    # Minimal fallback if repo file not found
    return (
        "Hey [Name],\n\n"
        "Your [project/skill] shows the [specific ability] I need. I’m John, a psychiatrist shipping an open clinical AI prototype.\n\n"
        "Looking forward,\nJohn"
    )
