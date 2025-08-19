from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    openai_api_key: str | None
    yc_match_url: str
    max_send: int


def load_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        yc_match_url=os.getenv("YC_MATCH_URL", "https://www.startupschool.org/cofounder-matching"),
        max_send=int(os.getenv("MAX_SEND", "5")),
    )
