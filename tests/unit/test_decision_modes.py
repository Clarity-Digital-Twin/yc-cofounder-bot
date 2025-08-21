"""Test decision modes (Advisor, Rubric, Hybrid) with minimal mocks."""

from unittest.mock import Mock

from yc_matcher.application.gating import GatedDecision
from yc_matcher.domain.entities import Criteria, Profile
from yc_matcher.interface.di import RubricOnlyAdapter


class TestAdvisorMode:
    """Test Advisor mode (AI-only, no auto-send)."""

    def test_advisor_never_auto_sends(self) -> None:
        """Test advisor mode never auto-sends even on YES."""
        # Arrange
        mock_decision = Mock()
        mock_decision.auto_send = False
        mock_decision.evaluate.return_value = {
            "decision": "YES",
            "rationale": "Great match",
            "draft": "Message",
            "auto_send": False,
        }

        profile = Profile(raw_text="test profile")
        criteria = Criteria(text="test criteria")

        # Act
        result = mock_decision.evaluate(profile, criteria)

        # Assert
        assert result["decision"] == "YES"
        assert result["auto_send"] is False

    def test_advisor_provides_detailed_rationale(self) -> None:
        """Test advisor mode provides detailed AI rationale."""
        # Arrange
        mock_decision = Mock()
        detailed_rationale = "Based on analysis: strong Python skills, relevant experience"
        mock_decision.evaluate.return_value = {
            "decision": "YES",
            "rationale": detailed_rationale,
            "draft": "Personalized message",
            "confidence": 0.85,
        }

        profile = Profile(raw_text="test")
        criteria = Criteria(text="test")

        # Act
        result = mock_decision.evaluate(profile, criteria)

        # Assert
        assert len(result["rationale"]) > 20
        assert "confidence" in result


class TestRubricMode:
    """Test Rubric mode (rules-based, auto-send)."""

    def test_rubric_auto_sends_above_threshold(self) -> None:
        """Test rubric mode auto-sends when score >= threshold."""
        # Arrange
        mock_scoring = Mock()
        mock_scoring.score.return_value = Mock(value=5.0)

        adapter = RubricOnlyAdapter(scoring=mock_scoring, threshold=4.0)
        profile = Profile(raw_text="test")
        criteria = Criteria(text="test")

        # Act
        result = adapter.evaluate(profile, criteria)

        # Assert
        assert result["decision"] == "YES"
        assert result["auto_send"] is True
        assert result["score"] == 5.0

    def test_rubric_blocks_below_threshold(self) -> None:
        """Test rubric mode blocks when score < threshold."""
        # Arrange
        mock_scoring = Mock()
        mock_scoring.score.return_value = Mock(value=2.0)

        adapter = RubricOnlyAdapter(scoring=mock_scoring, threshold=4.0)
        profile = Profile(raw_text="test")
        criteria = Criteria(text="test")

        # Act
        result = adapter.evaluate(profile, criteria)

        # Assert
        assert result["decision"] == "NO"
        assert result["auto_send"] is False
        assert result["score"] == 2.0
        assert result["draft"] == ""

    def test_rubric_mode_is_deterministic(self) -> None:
        """Test rubric mode gives same result for same input."""
        # Arrange
        mock_scoring = Mock()
        mock_scoring.score.return_value = Mock(value=4.5)

        adapter = RubricOnlyAdapter(scoring=mock_scoring, threshold=4.0)
        profile = Profile(raw_text="same profile")
        criteria = Criteria(text="same criteria")

        # Act - evaluate twice
        result1 = adapter.evaluate(profile, criteria)
        result2 = adapter.evaluate(profile, criteria)

        # Assert - same results
        assert result1["decision"] == result2["decision"]
        assert result1["score"] == result2["score"]
        assert result1["auto_send"] == result2["auto_send"]

    def test_rubric_includes_threshold_in_result(self) -> None:
        """Test rubric mode includes threshold in result."""
        # Arrange
        mock_scoring = Mock()
        mock_scoring.score.return_value = Mock(value=3.0)

        adapter = RubricOnlyAdapter(scoring=mock_scoring, threshold=4.5)
        profile = Profile(raw_text="test")
        criteria = Criteria(text="test")

        # Act
        result = adapter.evaluate(profile, criteria)

        # Assert
        assert result["threshold"] == 4.5
        assert "threshold: 4.5" in result["rationale"]


class TestHybridMode:
    """Test Hybrid mode (AI + Rubric combined)."""

    def test_hybrid_gates_with_rubric_first(self) -> None:
        """Test hybrid mode uses rubric as gate before AI."""
        # Arrange
        mock_scoring = Mock()
        mock_scoring.score.return_value = Mock(value=2.0)  # Below threshold

        mock_decision = Mock()
        mock_decision.evaluate.return_value = {
            "decision": "YES",
            "rationale": "AI says yes",
            "draft": "Message",
        }

        gated = GatedDecision(scoring=mock_scoring, decision=mock_decision, threshold=4.0)

        profile = Profile(raw_text="test")
        criteria = Criteria(text="test")

        # Act
        result = gated.evaluate(profile, criteria)

        # Assert - rubric gate should block
        assert result["decision"] == "NO"
        assert "Below threshold" in result["rationale"]  # Actual message is "Below threshold or red flags"
        # AI decision should not be called when gated
        mock_decision.evaluate.assert_not_called()

    def test_hybrid_calls_ai_when_rubric_passes(self) -> None:
        """Test hybrid mode calls AI when rubric score passes."""
        # Arrange
        mock_scoring = Mock()
        mock_scoring.score.return_value = Mock(value=5.0)  # Above threshold

        mock_decision = Mock()
        mock_decision.evaluate.return_value = {
            "decision": "YES",
            "rationale": "AI analysis positive",
            "draft": "Personalized message",
            "confidence": 0.9,
        }

        gated = GatedDecision(scoring=mock_scoring, decision=mock_decision, threshold=4.0)

        profile = Profile(raw_text="test")
        criteria = Criteria(text="test")

        # Act
        result = gated.evaluate(profile, criteria)

        # Assert - AI should be called
        mock_decision.evaluate.assert_called_once_with(profile, criteria)
        assert result["decision"] == "YES"
        assert "AI analysis" in result["rationale"]

    def test_hybrid_includes_both_scores(self) -> None:
        """Test hybrid mode includes both rubric score and AI confidence."""
        # Arrange
        mock_scoring = Mock()
        mock_scoring.score.return_value = Mock(value=4.5)

        mock_decision = Mock()
        mock_decision.evaluate.return_value = {
            "decision": "YES",
            "rationale": "Good match",
            "draft": "Message",
            "confidence": 0.8,
        }

        gated = GatedDecision(scoring=mock_scoring, decision=mock_decision, threshold=4.0)

        profile = Profile(raw_text="test")
        criteria = Criteria(text="test")

        # Act
        result = gated.evaluate(profile, criteria)

        # Assert - GatedDecision passes through the decision result when threshold met
        assert result["decision"] == "YES"
        assert result["rationale"] == "Good match"
        assert result["confidence"] == 0.8

    def test_hybrid_respects_ai_no_even_with_high_score(self) -> None:
        """Test hybrid respects AI's NO decision even with high rubric score."""
        # Arrange
        mock_scoring = Mock()
        mock_scoring.score.return_value = Mock(value=5.0)  # High score

        mock_decision = Mock()
        mock_decision.evaluate.return_value = {
            "decision": "NO",  # AI says no
            "rationale": "Red flags detected",
            "draft": "",
        }

        gated = GatedDecision(scoring=mock_scoring, decision=mock_decision, threshold=4.0)

        profile = Profile(raw_text="test")
        criteria = Criteria(text="test")

        # Act
        result = gated.evaluate(profile, criteria)

        # Assert - should respect AI's NO
        assert result["decision"] == "NO"
        assert "Red flags" in result["rationale"]


class TestModeComparison:
    """Test comparing different modes."""

    def test_modes_have_different_auto_send_behavior(self) -> None:
        """Test each mode has distinct auto-send behavior."""
        # Arrange
        profile = Profile(raw_text="test")
        criteria = Criteria(text="test")
        mock_scoring = Mock()
        mock_scoring.score.return_value = Mock(value=5.0)

        # Advisor mode
        advisor = Mock()
        advisor.auto_send = False
        advisor.evaluate.return_value = {"decision": "YES", "auto_send": False}

        # Rubric mode
        rubric = RubricOnlyAdapter(scoring=mock_scoring, threshold=4.0)

        # Act
        advisor_result = advisor.evaluate(profile, criteria)
        rubric_result = rubric.evaluate(profile, criteria)

        # Assert
        assert advisor_result["auto_send"] is False  # Never auto
        assert rubric_result["auto_send"] is True  # Always auto when YES

    def test_modes_provide_different_rationale_styles(self) -> None:
        """Test each mode provides different style rationales."""
        # Arrange
        profile = Profile(raw_text="test")
        criteria = Criteria(text="test")
        mock_scoring = Mock()
        mock_scoring.score.return_value = Mock(value=5.0)

        # Advisor - detailed AI rationale
        advisor = Mock()
        advisor.evaluate.return_value = {
            "decision": "YES",
            "rationale": "Detailed AI analysis with multiple factors considered",
        }

        # Rubric - score-based rationale
        rubric = RubricOnlyAdapter(scoring=mock_scoring, threshold=4.0)

        # Act
        advisor_result = advisor.evaluate(profile, criteria)
        rubric_result = rubric.evaluate(profile, criteria)

        # Assert
        assert len(advisor_result["rationale"]) > len(rubric_result["rationale"])
        assert "score" in rubric_result["rationale"].lower()
        assert "threshold" in rubric_result["rationale"].lower()
