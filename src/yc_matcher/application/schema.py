from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Extracted(BaseModel):
    name: str | None = None
    tags: list[str] = Field(default_factory=list)


class DecisionDTO(BaseModel):
    decision: Literal["YES", "NO"]
    rationale: str
    draft: str = ""
    extracted: Extracted = Field(default_factory=Extracted)
    prompt_version: str | None = None
