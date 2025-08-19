from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class Criteria:
    text: str
    # Optional parsed keywords for rubric scoring
    keywords: Optional[List[str]] = None


@dataclass(frozen=True)
class Profile:
    raw_text: str
    name_hint: Optional[str] = None


@dataclass(frozen=True)
class Score:
    value: float
    reasons: List[str]


@dataclass(frozen=True)
class Decision:
    yes: bool
    rationale: str
    draft: str
    extracted_name: Optional[str] = None
