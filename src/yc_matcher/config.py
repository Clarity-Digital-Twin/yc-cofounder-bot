"""Configuration module - single source of truth for all env vars.

Following the principle: Environment variables are ONLY read here.
All other modules get config through this interface.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    """Legacy settings for backward compatibility."""
    openai_api_key: str | None
    yc_match_url: str
    max_send: int


def load_settings() -> Settings:
    """Legacy loader - kept for compatibility."""
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        yc_match_url=os.getenv("YC_MATCH_URL", "https://www.startupschool.org/cofounder-matching"),
        max_send=int(os.getenv("MAX_SEND", "5")),
    )


# ============================================================================
# AI-ONLY MODE CONFIGURATION
# Single source of truth for all environment variables
# ============================================================================

def get_decision_model() -> str:
    """Get the AI decision model to use.
    
    Precedence:
    1. DECISION_MODEL_RESOLVED (from runtime discovery)
    2. OPENAI_DECISION_MODEL (from .env)
    3. Default to gpt-4o
    """
    return (
        os.getenv("DECISION_MODEL_RESOLVED") or
        os.getenv("OPENAI_DECISION_MODEL") or
        "gpt-4o"
    )


def get_cua_model() -> str | None:
    """Get the Computer Use model if available.
    
    Precedence:
    1. CUA_MODEL_RESOLVED (from runtime discovery)
    2. CUA_MODEL (from .env)
    3. None if not configured
    """
    return os.getenv("CUA_MODEL_RESOLVED") or os.getenv("CUA_MODEL")


def get_auto_send_default() -> bool:
    """Whether to auto-send messages on match (default: False for safety)."""
    return os.getenv("AUTO_SEND", "0") == "1"


def is_shadow_mode() -> bool:
    """Whether we're in shadow mode (evaluate only, never send)."""
    return os.getenv("SHADOW_MODE", "0") == "1"


def is_openai_enabled() -> bool:
    """Whether OpenAI integration is enabled."""
    return os.getenv("ENABLE_OPENAI", "0") in {"1", "true", "True"}


def is_cua_enabled() -> bool:
    """Whether Computer Use API is enabled as planner."""
    return os.getenv("ENABLE_CUA", "0") in {"1", "true", "True"}


def is_playwright_enabled() -> bool:
    """Whether Playwright browser automation is enabled."""
    return os.getenv("ENABLE_PLAYWRIGHT", "0") in {"1", "true", "True"}


def get_daily_quota() -> int:
    """Daily message quota."""
    return int(os.getenv("DAILY_QUOTA", "25"))


def get_weekly_quota() -> int:
    """Weekly message quota."""
    return int(os.getenv("WEEKLY_QUOTA", "120"))


def get_pace_seconds() -> int:
    """Minimum seconds between sends."""
    return int(os.getenv("PACE_MIN_SECONDS", "45"))


def get_openai_api_key() -> str | None:
    """OpenAI API key."""
    return os.getenv("OPENAI_API_KEY")


def get_yc_credentials() -> tuple[str | None, str | None]:
    """YC login credentials for auto-login."""
    return os.getenv("YC_EMAIL"), os.getenv("YC_PASSWORD")


def is_calendar_quota_enabled() -> bool:
    """Whether to use calendar-aware quota tracking."""
    return os.getenv("ENABLE_CALENDAR_QUOTA", "0") in {"1", "true", "True"}


def get_playwright_fallback_enabled() -> bool:
    """Whether to fallback to Playwright when CUA fails."""
    return os.getenv("ENABLE_PLAYWRIGHT_FALLBACK", "1") == "1"
