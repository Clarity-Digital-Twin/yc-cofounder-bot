from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

MAX_CHARS = 500


class TemplateRenderer:
    def __init__(self, template: str, banned_phrases: list[str] | None = None) -> None:
        self.template = template
        self.banned = [bp.lower() for bp in (banned_phrases or [])]

    def render(self, decision: Mapping[str, Any]) -> str:
        name = (
            (decision.get("extracted", {}) or {}).get("name")
            if isinstance(decision.get("extracted"), dict)
            else None
        ) or "there"
        text = (
            self.template.replace("[Name]", str(name))
            .replace("[project/skill]", "work")
            .replace("[specific ability]", "skills")
        )
        # Remove unknown square-bracket placeholders
        text = re.sub(r"\[[^\]]+\]", "", text)
        # Remove banned phrases
        for bp in self.banned:
            text = re.sub(re.escape(bp), "", text, flags=re.IGNORECASE)
        # Clamp to max chars
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS]
        return text.strip()
