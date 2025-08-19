from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Decision:
    decision: str  # "YES" | "NO"
    rationale: str
    message: str


def _extract_name(profile_text: str) -> str:
    # Simple heuristic: first non-empty line is a name
    for line in profile_text.splitlines():
        line = line.strip()
        if line and all(c.isalpha() or c.isspace() or c in "-'" for c in line):
            parts = [p for p in line.split() if p]
            if parts:
                return parts[0]
    return "there"


def _match_score(profile_text: str, keywords: List[str]) -> int:
    text = profile_text.lower()
    return sum(1 for kw in keywords if kw.lower() in text)


def decide_and_draft(criteria: str, profile_text: str, template: str) -> Decision:
    """
    MVP heuristic decisioner. Later, replace with OpenAI model call.
    """
    # Extract simple keyword list from criteria (split by commas or newlines)
    raw_keys = [k.strip() for k in criteria.replace("\n", ",").split(",")]
    keywords = [k for k in raw_keys if k]
    score = _match_score(profile_text, keywords) if keywords else 0

    if keywords and score == 0:
        return Decision(
            decision="NO",
            rationale="No strong alignment with provided criteria keywords.",
            message="",
        )

    # Decide YES with brief rationale
    rationale = (
        "Matches several criteria keywords." if score >= 2 else "Potential fit; partial keyword match."
    ) if keywords else "No specific keywords provided; using general fit."

    name = _extract_name(profile_text)

    # Fill minimal variables in template
    draft = (
        template
        .replace("[Name]", name)
        .replace("[project/skill]", "work")
        .replace("[specific ability]", "skills")
    )

    return Decision(decision="YES", rationale=rationale, message=draft)
