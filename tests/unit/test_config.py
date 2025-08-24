"""Unit tests for config module."""

import os
from unittest.mock import patch

import pytest

from yc_matcher import config


class TestConfigModule:
    """Test configuration functions."""

    def test_default_values(self) -> None:
        """Test that default values are returned when env vars are not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert config.get_daily_quota() == 25
            assert config.get_weekly_quota() == 120
            assert config.is_shadow_mode() is False
            assert config.is_openai_enabled() is False
            assert config.is_cua_enabled() is False
            assert config.is_playwright_enabled() is False  # Default is False
            assert config.get_cua_model() is None
            assert config.get_decision_model() == "gpt-4o"  # Default per config.py
            assert config.get_cua_max_turns() == 40
            assert config.get_auto_send_default() is False
            assert config.is_headless() is False  # Default is False (PLAYWRIGHT_HEADLESS=0)
            assert config.is_debug_mode() is False

    def test_env_var_parsing(self) -> None:
        """Test that env vars are correctly parsed."""
        with patch.dict(
            os.environ,
            {
                "DAILY_QUOTA": "50",
                "WEEKLY_QUOTA": "200",
                "SHADOW_MODE": "1",
                "OPENAI_API_KEY": "sk-test",
                "ENABLE_OPENAI": "1",  # Need this flag too
                "ENABLE_CUA": "1",
                "ENABLE_PLAYWRIGHT": "0",
                "CUA_MODEL": "test-cua-model",
                "OPENAI_DECISION_MODEL": "gpt-5",  # Use env var name from config.py
                "CUA_MAX_TURNS": "50",
                "YC_EMAIL": "test@example.com",
                "YC_PASSWORD": "secret",
                "AUTO_SEND": "1",  # Correct env var name
                "PLAYWRIGHT_HEADLESS": "0",
                "DEBUG_MODE": "1",
            },
        ):
            assert config.get_daily_quota() == 50
            assert config.get_weekly_quota() == 200
            assert config.is_shadow_mode() is True
            assert config.is_openai_enabled() is True  # Has API key AND flag
            assert config.is_cua_enabled() is True
            assert config.is_playwright_enabled() is False
            assert config.get_cua_model() == "test-cua-model"
            assert config.get_decision_model() == "gpt-5"
            assert config.get_cua_max_turns() == 50
            credentials = config.get_yc_credentials()
            assert credentials[0] == "test@example.com"
            assert credentials[1] == "secret"
            assert config.get_auto_send_default() is True
            assert config.is_headless() is False
            assert config.is_debug_mode() is True

    def test_boolean_parsing(self) -> None:
        """Test that boolean env vars handle various truthy values."""
        truthy_values = ["1", "true", "True"]  # Only these are actually accepted
        falsy_values = ["0", "false", "False", "FALSE", "no", "No", "NO", "", "2", "TRUE", "yes", "Yes", "YES"]  # Everything else is falsy

        for val in truthy_values:
            with patch.dict(os.environ, {"SHADOW_MODE": val}):
                assert config.is_shadow_mode() is True, f"Failed for value: {val}"

        for val in falsy_values:
            with patch.dict(os.environ, {"SHADOW_MODE": val}):
                assert config.is_shadow_mode() is False, f"Failed for value: {val}"

    def test_invalid_numeric_values(self) -> None:
        """Test that invalid numeric values raise ValueError."""
        with patch.dict(os.environ, {"DAILY_QUOTA": "invalid"}):
            with pytest.raises(ValueError):
                config.get_daily_quota()

        with patch.dict(os.environ, {"CUA_MAX_TURNS": "abc"}):
            with pytest.raises(ValueError):
                config.get_cua_max_turns()

    def test_decision_model_resolved(self) -> None:
        """Test DECISION_MODEL_RESOLVED override."""
        with patch.dict(
            os.environ,
            {
                "OPENAI_DECISION_MODEL": "gpt-5",  # Use env var name from config.py
                "DECISION_MODEL_RESOLVED": "gpt-5",
            },
        ):
            assert config.get_decision_model() == "gpt-5"  # Resolved takes precedence

    def test_cua_model_resolved(self) -> None:
        """Test CUA_MODEL_RESOLVED override."""
        with patch.dict(
            os.environ,
            {
                "CUA_MODEL": "model-1",
                "CUA_MODEL_RESOLVED": "model-2",
            },
        ):
            assert config.get_cua_model() == "model-2"  # Resolved takes precedence

    def test_openai_enabled_requires_api_key(self) -> None:
        """Test that OpenAI is only enabled when API key is present."""
        with patch.dict(os.environ, {}, clear=True):
            assert config.is_openai_enabled() is False  # No API key, no flag

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            assert config.is_openai_enabled() is False  # Has API key but no flag

        with patch.dict(os.environ, {"ENABLE_OPENAI": "1", "OPENAI_API_KEY": "sk-test"}):
            assert config.is_openai_enabled() is True  # Has both AND flag

    def test_empty_string_handling(self) -> None:
        """Test that empty strings are handled correctly."""
        with patch.dict(os.environ, {"YC_EMAIL": "", "YC_PASSWORD": ""}):
            credentials = config.get_yc_credentials()
            assert credentials[0] == ""  # Empty string returned as-is
            assert credentials[1] == ""

        with patch.dict(os.environ, {"CUA_MODEL": "", "OPENAI_DECISION_MODEL": ""}):
            assert config.get_cua_model() == ""  # Empty string returned as-is
            assert config.get_decision_model() == "gpt-4o"  # Default per config.py (empty string triggers default)

    def test_gpt5_configuration(self) -> None:
        """Test GPT-5 specific configuration functions."""
        # Test defaults
        with patch.dict(os.environ, {}, clear=True):
            assert config.get_gpt5_max_tokens() == 4000
            assert config.get_gpt5_temperature() == 0.3
            assert config.get_gpt5_top_p() == 0.9
            assert config.get_service_tier() == "auto"

        # Test custom values
        with patch.dict(os.environ, {
            "GPT5_MAX_TOKENS": "8000",
            "GPT5_TEMPERATURE": "0.7",
            "GPT5_TOP_P": "0.95",
            "SERVICE_TIER": "priority"
        }):
            assert config.get_gpt5_max_tokens() == 8000
            assert config.get_gpt5_temperature() == 0.7
            assert config.get_gpt5_top_p() == 0.95
            assert config.get_service_tier() == "priority"
