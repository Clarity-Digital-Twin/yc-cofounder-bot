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
    3. Default to gpt-4o (current GPT-4 class model)
    """
    return os.getenv("DECISION_MODEL_RESOLVED") or os.getenv("OPENAI_DECISION_MODEL") or "gpt-4o"


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
    return os.getenv("AUTO_SEND", "0") in {"1", "true", "True"}


def is_shadow_mode() -> bool:
    """Whether we're in shadow mode (evaluate only, never send)."""
    return os.getenv("SHADOW_MODE", "0") in {"1", "true", "True"}


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
    return os.getenv("ENABLE_PLAYWRIGHT_FALLBACK", "1") in {"1", "true", "True"}


def is_headless() -> bool:
    """Whether to run browser in headless mode."""
    return os.getenv("PLAYWRIGHT_HEADLESS", "0") in {"1", "true", "True"}


def use_three_input_ui() -> bool:
    """Whether to use the three-input UI mode."""
    return os.getenv("USE_THREE_INPUT_UI", "false").lower() in {"true", "1", "yes"}


def get_cua_max_turns() -> int:
    """Maximum turns for CUA loop."""
    return int(os.getenv("CUA_MAX_TURNS", "40"))


def get_cua_temperature() -> float:
    """Temperature for CUA model."""
    return float(os.getenv("CUA_TEMPERATURE", "0.3"))


def get_cua_max_tokens() -> int:
    """Max tokens for CUA model."""
    return int(os.getenv("CUA_MAX_TOKENS", "1200"))


def get_auto_browse_limit() -> int:
    """Default limit for auto-browsing profiles."""
    return int(os.getenv("AUTO_BROWSE_LIMIT", "10"))


def is_debug_mode() -> bool:
    """Whether to enable debug logging and verbose output."""
    return os.getenv("DEBUG_MODE", "0") in {"1", "true", "True"}


def get_log_level() -> str:
    """Get logging level (DEBUG, INFO, WARNING, ERROR)."""
    return os.getenv("LOG_LEVEL", "DEBUG" if is_debug_mode() else "INFO")


def get_playwright_browsers_path() -> str | None:
    """Get the path where Playwright browsers are installed."""
    return os.getenv("PLAYWRIGHT_BROWSERS_PATH")


# ============================================================================
# GPT-5 SPECIFIC CONFIGURATION (Context7-verified parameters)
# ============================================================================


def get_gpt5_max_tokens() -> int:
    """Get max output tokens for GPT-5 (up to 128,000 per Context7 docs)."""
    return int(os.getenv("GPT5_MAX_TOKENS", "4000"))


def get_gpt5_temperature() -> float:
    """Get temperature for GPT-5 (0-2 range per Context7 docs)."""
    return float(os.getenv("GPT5_TEMPERATURE", "0.3"))


def get_gpt5_top_p() -> float:
    """Get top_p for GPT-5 nucleus sampling (0-1 range)."""
    return float(os.getenv("GPT5_TOP_P", "0.9"))


def get_service_tier() -> str:
    """Get service tier for API requests (auto, default, flex, priority)."""
    return os.getenv("SERVICE_TIER", "auto")


def get_gpt5_verbosity() -> str:
    """Get verbosity for GPT-5 text responses (low, medium, high per Context7 docs)."""
    return os.getenv("GPT5_VERBOSITY", "low")


def get_gpt5_reasoning_effort() -> str:
    """Get reasoning effort for GPT-5 (minimal, low, medium, high per Context7 docs)."""
    return os.getenv("GPT5_REASONING_EFFORT", "minimal")
