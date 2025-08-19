from __future__ import annotations

from typing import Literal, List, Optional
from pydantic import BaseModel, Field


class Extracted(BaseModel):
    name: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class DecisionDTO(BaseModel):
    decision: Literal["YES", "NO"]
    rationale: str
    draft: str = ""
    extracted: Extracted = Field(default_factory=Extracted)
    prompt_version: Optional[str] = None
