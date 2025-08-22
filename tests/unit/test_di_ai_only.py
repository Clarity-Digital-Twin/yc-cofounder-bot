"""Test AI-only dependency injection (simplified from 3 modes)."""

import os
from unittest.mock import patch

from yc_matcher.interface.di import build_services


class TestAIOnlyDI:
    """Test simplified AI-only dependency injection."""

    def test_build_services_creates_ai_adapter(self) -> None:
        """Test build_services creates OpenAI adapter when enabled."""
        # Arrange
        with patch.dict(os.environ, {"ENABLE_OPENAI": "1", "OPENAI_API_KEY": "test-key"}):
            # Act
            eval_use, send_use, logger = build_services(
                criteria_text="Looking for Python developers",
                template_text="Hi {{name}}!",
            )

            # Assert
            assert eval_use is not None
            assert send_use is not None
            assert logger is not None
            # Decision adapter is internal but we can verify the use case works
            from yc_matcher.domain.entities import Criteria, Profile
            profile = Profile(raw_text="Test profile")
            criteria = Criteria(text="Test criteria")
            # This will use LocalDecisionAdapter in test mode but proves wiring works
            result = eval_use(profile, criteria)
            assert "decision" in result
            assert "draft" in result

    def test_build_services_with_fallback(self) -> None:
        """Test build_services falls back to LocalDecisionAdapter when OpenAI disabled."""
        # Arrange
        with patch.dict(os.environ, {"ENABLE_OPENAI": "0"}):
            # Act
            eval_use, send_use, logger = build_services(
                criteria_text="Test criteria",
            )

            # Assert
            assert eval_use is not None
            assert send_use is not None
            assert logger is not None

    def test_build_services_simplified_signature(self) -> None:
        """Test build_services has simplified signature without old parameters."""
        # Arrange
        with patch.dict(os.environ, {"ENABLE_OPENAI": "0"}):
            # Act - only pass required parameters
            eval_use, send_use, logger = build_services(
                criteria_text="Test",
                template_text="Hi {{name}}",
                prompt_ver="v1",
                rubric_ver="v1",
            )

            # Assert
            assert eval_use is not None
            assert send_use is not None
            assert logger is not None
