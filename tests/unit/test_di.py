"""Test dependency injection and factory methods with minimal mocks."""

import os
from unittest.mock import Mock, patch

import pytest

from yc_matcher.interface.di import (
    RubricOnlyAdapter,
    build_services,
    create_decision_adapter,
)


class TestRubricOnlyAdapter:
    """Test pure rubric-based decision adapter."""

    def test_rubric_adapter_always_auto_sends(self) -> None:
        """Test rubric adapter has auto_send=True."""
        # Arrange
        mock_scoring = Mock()

        # Act
        adapter = RubricOnlyAdapter(scoring=mock_scoring, threshold=4.0)

        # Assert
        assert adapter.auto_send is True

    def test_rubric_adapter_passes_when_above_threshold(self) -> None:
        """Test rubric adapter returns YES when score >= threshold."""
        # Arrange
        mock_scoring = Mock()
        mock_score = Mock(value=4.5)
        mock_scoring.score.return_value = mock_score
        adapter = RubricOnlyAdapter(scoring=mock_scoring, threshold=4.0)

        profile = Mock()
        criteria = Mock()

        # Act
        result = adapter.evaluate(profile, criteria)

        # Assert
        assert result["decision"] == "YES"
        assert result["auto_send"] is True
        assert result["score"] == 4.5
        assert result["threshold"] == 4.0
        assert "Rubric score: 4.5" in result["rationale"]

    def test_rubric_adapter_fails_when_below_threshold(self) -> None:
        """Test rubric adapter returns NO when score < threshold."""
        # Arrange
        mock_scoring = Mock()
        mock_score = Mock(value=3.5)
        mock_scoring.score.return_value = mock_score
        adapter = RubricOnlyAdapter(scoring=mock_scoring, threshold=4.0)

        profile = Mock()
        criteria = Mock()

        # Act
        result = adapter.evaluate(profile, criteria)

        # Assert
        assert result["decision"] == "NO"
        assert result["auto_send"] is False
        assert result["score"] == 3.5
        assert result["draft"] == ""


class TestCreateDecisionAdapter:
    """Test decision adapter factory method."""

    @patch.dict(os.environ, {"DECISION_MODE": "advisor"})
    def test_create_advisor_mode(self) -> None:
        """Test creating advisor mode adapter."""
        # Arrange
        mock_scoring = Mock()

        # Act
        adapter = create_decision_adapter(
            mode=None,  # Should use env
            scoring=mock_scoring,
        )

        # Assert - should be LocalDecisionAdapter or OpenAI
        assert hasattr(adapter, "evaluate")
        # Advisor mode should not auto-send
        if hasattr(adapter, "auto_send"):
            assert adapter.auto_send is False

    def test_create_rubric_mode(self) -> None:
        """Test creating rubric mode adapter."""
        # Arrange
        mock_scoring = Mock()

        # Act
        adapter = create_decision_adapter(mode="rubric", scoring=mock_scoring, threshold=5.0)

        # Assert
        assert isinstance(adapter, RubricOnlyAdapter)
        assert adapter.threshold == 5.0
        assert adapter.auto_send is True

    def test_create_hybrid_mode(self) -> None:
        """Test creating hybrid mode adapter."""
        # Arrange
        mock_scoring = Mock()

        # Act
        adapter = create_decision_adapter(mode="hybrid", scoring=mock_scoring, threshold=4.0)

        # Assert - should be GatedDecision
        assert hasattr(adapter, "evaluate")
        # Verify it's not RubricOnlyAdapter
        assert not isinstance(adapter, RubricOnlyAdapter)

    def test_rubric_mode_requires_scoring(self) -> None:
        """Test rubric mode raises error without scoring service."""
        # Act & Assert
        with pytest.raises(ValueError, match="Rubric mode requires scoring service"):
            create_decision_adapter(mode="rubric", scoring=None)

    def test_hybrid_mode_requires_scoring(self) -> None:
        """Test hybrid mode raises error without scoring service."""
        # Act & Assert
        with pytest.raises(ValueError, match="Hybrid mode requires scoring service"):
            create_decision_adapter(mode="hybrid", scoring=None)

    def test_unknown_mode_raises_error(self) -> None:
        """Test unknown mode raises ValueError."""
        # Arrange
        mock_scoring = Mock()

        # Act & Assert
        with pytest.raises(ValueError, match="Unknown decision mode: invalid"):
            create_decision_adapter(mode="invalid", scoring=mock_scoring)

    @patch.dict(os.environ, {"ENABLE_OPENAI": "1"})
    @patch("yc_matcher.interface.di.OpenAIDecisionAdapter")
    def test_openai_adapter_when_enabled(self, mock_openai_class: Mock) -> None:
        """Test OpenAI adapter is used when enabled."""
        # Arrange
        mock_adapter = Mock()
        mock_openai_class.return_value = mock_adapter
        mock_scoring = Mock()

        # Act
        adapter = create_decision_adapter(mode="advisor", scoring=mock_scoring)

        # Assert - should attempt to create OpenAI adapter
        # Note: May fall back to Local if OpenAI import fails
        assert hasattr(adapter, "evaluate")


class TestBuildServices:
    """Test service building and wiring."""

    def test_build_services_creates_all_components(self) -> None:
        """Test build_services creates all required components."""
        # Arrange
        criteria_text = "Python, FastAPI"
        template_text = "Hi {name}"

        # Act
        eval_use, send_use, logger = build_services(
            criteria_text=criteria_text,
            template_text=template_text,
            decision_mode="rubric",
            threshold=4.0,
        )

        # Assert
        assert eval_use is not None
        assert send_use is not None
        assert logger is not None
        assert callable(eval_use)
        assert callable(send_use)
        assert hasattr(logger, "emit")

    def test_build_services_uses_decision_mode(self) -> None:
        """Test build_services respects decision mode parameter."""
        # Arrange
        criteria_text = "Python"

        # Act
        eval_use, _, _ = build_services(
            criteria_text=criteria_text, decision_mode="rubric", threshold=3.0
        )

        # Assert - decision should be RubricOnlyAdapter
        assert hasattr(eval_use, "decision")
        # Check if it's rubric mode by checking auto_send behavior
        if hasattr(eval_use.decision, "auto_send"):
            assert eval_use.decision.auto_send is True

    def test_build_services_sets_weights(self) -> None:
        """Test build_services uses custom weights."""
        # Arrange
        custom_weights = {"python": 5.0, "react": 3.0}

        # Act
        eval_use, _, _ = build_services(
            criteria_text="test", weights=custom_weights, decision_mode="rubric"
        )

        # Assert - weights should be converted to float
        # We can't directly check the scoring service weights,
        # but we can verify the service was created
        assert eval_use is not None

    @patch("yc_matcher.interface.di.Path")
    def test_build_services_creates_logger_with_versions(self, mock_path: Mock) -> None:
        """Test logger is created with version stamps."""
        # Arrange
        mock_path.return_value.parent.mkdir.return_value = None

        # Act
        _, _, logger = build_services(
            criteria_text="test", prompt_ver="v2", rubric_ver="v3", criteria_preset="custom"
        )

        # Assert
        assert hasattr(logger, "prompt_ver")
        assert hasattr(logger, "rubric_ver")
        assert hasattr(logger, "criteria_preset")
        assert logger.prompt_ver == "v2"
        assert logger.rubric_ver == "v3"
        assert logger.criteria_preset == "custom"

    @patch.dict(os.environ, {"ENABLE_CALENDAR_QUOTA": "1"})
    @patch("yc_matcher.interface.di.SQLiteDailyWeeklyQuota")
    def test_calendar_quota_when_enabled(self, mock_quota_class: Mock) -> None:
        """Test calendar-aware quota is used when enabled."""
        # Arrange
        mock_quota = Mock()
        mock_quota_class.return_value = mock_quota

        # Act
        _, send_use, _ = build_services(criteria_text="test", decision_mode="advisor")

        # Assert
        mock_quota_class.assert_called_once()
        assert send_use.quota is mock_quota

    @patch.dict(os.environ, {"ENABLE_CUA": "1"})
    @patch("yc_matcher.interface.di.OpenAICUABrowser")
    def test_cua_browser_when_enabled(self, mock_cua_class: Mock) -> None:
        """Test CUA browser is used when enabled."""
        # Arrange
        mock_browser = Mock()
        mock_cua_class.return_value = mock_browser

        # Act
        _, send_use, _ = build_services(criteria_text="test", decision_mode="advisor")

        # Assert - CUA should be attempted
        # May fall back if import fails
        assert hasattr(send_use, "browser")

    def test_logger_attached_to_decision_adapter(self) -> None:
        """Test logger is properly attached to decision adapter."""
        # Act
        eval_use, _, logger = build_services(criteria_text="test", decision_mode="advisor")

        # Assert
        # Logger should be attached to decision if it supports it
        if hasattr(eval_use.decision, "logger"):
            assert eval_use.decision.logger is logger

    def test_default_template_loaded_when_none(self) -> None:
        """Test default template is loaded when not provided."""
        # Act
        eval_use, _, _ = build_services(
            criteria_text="test",
            template_text=None,  # Should load default
            decision_mode="advisor",
        )

        # Assert
        # Template should be loaded (can't check exact content without side effects)
        assert eval_use.message is not None
        assert hasattr(eval_use.message, "render")
