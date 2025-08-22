"""Test that hybrid mode returns draft even when decision is NO.

Following TDD: Test that GatedDecision always gets AI draft.
"""

from unittest.mock import MagicMock

from yc_matcher.application.gating import GatedDecision
from yc_matcher.application.ports import DecisionPort, ScoringPort
from yc_matcher.domain.entities import Criteria, Profile, Score


class TestHybridDraft:
    """Test that hybrid mode properly generates drafts."""

    def test_hybrid_returns_draft_on_yes_decision(self) -> None:
        """Test that hybrid mode returns draft when above threshold."""
        # Arrange
        mock_scoring = MagicMock(spec=ScoringPort)
        mock_scoring.score.return_value = Score(value=5.0, details={})  # Above threshold

        mock_decision = MagicMock(spec=DecisionPort)
        mock_decision.evaluate.return_value = {
            "decision": "YES",
            "rationale": "Great match!",
            "draft": "Hi there, I'd love to connect about your project...",
            "confidence": 0.9,
        }

        gated = GatedDecision(
            scoring=mock_scoring,
            decision=mock_decision,
            threshold=4.0,
        )

        profile = Profile(raw_text="Test profile")
        criteria = Criteria(text="Test criteria")

        # Act
        result = gated.evaluate(profile, criteria)

        # Assert
        assert result["decision"] == "YES"
        assert result["draft"] == "Hi there, I'd love to connect about your project..."
        assert result["score"] == 5.0
        assert "rationale" in result

        # AI should have been called
        mock_decision.evaluate.assert_called_once_with(profile, criteria)

    def test_hybrid_returns_draft_on_no_decision_below_threshold(self) -> None:
        """Test that hybrid mode returns AI draft even when forcing NO due to threshold."""
        # Arrange
        mock_scoring = MagicMock(spec=ScoringPort)
        mock_scoring.score.return_value = Score(value=2.0, details={})  # Below threshold

        mock_decision = MagicMock(spec=DecisionPort)
        mock_decision.evaluate.return_value = {
            "decision": "YES",  # AI thinks YES
            "rationale": "Interesting profile",
            "draft": "Hey, your background in ML is exactly what I need...",
            "confidence": 0.8,
        }

        gated = GatedDecision(
            scoring=mock_scoring,
            decision=mock_decision,
            threshold=4.0,
        )

        profile = Profile(raw_text="Test profile with ML experience")
        criteria = Criteria(text="Looking for ML expertise")

        # Act
        result = gated.evaluate(profile, criteria)

        # Assert
        assert result["decision"] == "NO"  # Overridden to NO due to threshold
        assert result["draft"] == "Hey, your background in ML is exactly what I need..."  # Still has draft
        assert result["score"] == 2.0
        assert "Below threshold" in result["rationale"]
        assert result["ai_decision"] == "YES"  # Track what AI originally said
        assert result["ai_rationale"] == "Interesting profile"

        # AI should have been called for draft
        mock_decision.evaluate.assert_called_once_with(profile, criteria)

    def test_hybrid_handles_red_flags(self) -> None:
        """Test that hybrid mode handles red flags properly."""
        # Arrange
        mock_scoring = MagicMock(spec=ScoringPort)
        mock_scoring.score.return_value = Score(value=-999.0, details={"crypto": -999})  # Red flag

        mock_decision = MagicMock(spec=DecisionPort)
        mock_decision.evaluate.return_value = {
            "decision": "YES",
            "rationale": "Could be interesting",
            "draft": "Your crypto project sounds innovative...",
            "confidence": 0.6,
        }

        gated = GatedDecision(
            scoring=mock_scoring,
            decision=mock_decision,
            threshold=4.0,
            red_flag_floor=-100.0,
        )

        profile = Profile(raw_text="Crypto enthusiast building DeFi")
        criteria = Criteria(text="No crypto")

        # Act
        result = gated.evaluate(profile, criteria)

        # Assert
        assert result["decision"] == "NO"  # Red flag forces NO
        assert result["draft"] == "Your crypto project sounds innovative..."  # Still has draft
        assert result["score"] == -999.0
        assert result["ai_decision"] == "YES"

        # AI should still be called for completeness
        mock_decision.evaluate.assert_called_once()

    def test_hybrid_handles_missing_draft(self) -> None:
        """Test that hybrid mode handles missing draft gracefully."""
        # Arrange
        mock_scoring = MagicMock(spec=ScoringPort)
        mock_scoring.score.return_value = Score(value=3.0, details={})

        mock_decision = MagicMock(spec=DecisionPort)
        mock_decision.evaluate.return_value = {
            "decision": "NO",
            "rationale": "Not a match",
            # No draft field
        }

        gated = GatedDecision(
            scoring=mock_scoring,
            decision=mock_decision,
            threshold=4.0,
        )

        profile = Profile(raw_text="Test")
        criteria = Criteria(text="Test")

        # Act
        result = gated.evaluate(profile, criteria)

        # Assert
        assert result["decision"] == "NO"
        assert result["draft"] == ""  # Empty string when missing
        assert result["score"] == 3.0
