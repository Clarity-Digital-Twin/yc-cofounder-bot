from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class Criteria:
    text: str
    # Optional parsed keywords for rubric scoring
    keywords: list[str] | None = None


@dataclass(frozen=True)
class Profile:
    raw_text: str
    name_hint: str | None = None


@dataclass(frozen=True)
class Score:
    value: float
    reasons: list[str] = field(default_factory=list)
    details: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Decision:
    yes: bool
    rationale: str
    draft: str
    extracted_name: str | None = None
