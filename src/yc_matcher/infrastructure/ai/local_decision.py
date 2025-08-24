from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from yc_matcher.application.ports import DecisionPort
from yc_matcher.domain.entities import Criteria, Profile


def _extract_name(profile_text: str) -> str:
    for line in profile_text.splitlines():
        line = line.strip()
        if line and all(c.isalpha() or c.isspace() or c in "-'" for c in line):
            parts = [p for p in line.split() if p]
            if parts:
                return parts[0]
    return "there"


class LocalDecisionAdapter(DecisionPort):
    """Simple local adapter producing rationale/extracted fields.

    Placeholder until OpenAI Decision adapter is wired.
    """

    def evaluate(self, profile: Profile, criteria: Criteria) -> Mapping[str, Any]:
        name = _extract_name(profile.raw_text)
        return {
            "decision": "YES",
            "rationale": "Matches criteria based on initial heuristic.",
            "extracted": {"name": name},
        }
