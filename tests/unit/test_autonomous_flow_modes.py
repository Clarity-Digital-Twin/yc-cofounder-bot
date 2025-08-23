"""Unit tests for autonomous flow mode logic."""

from yc_matcher.application.autonomous_flow import AutonomousFlow


class TestAutoSendLogic:
    """Test the _should_auto_send logic for all modes."""

    def test_advisor_mode_never_auto_sends(self) -> None:
        """Advisor mode requires HIL approval, never auto-sends."""
        flow = AutonomousFlow(None, None, None, None, None, None, None)  # type: ignore
        evaluation = {"decision": "YES", "draft": "Hi!", "score": 1.0}

        should_send = flow._should_auto_send(evaluation, "advisor", False, 0.5)

        assert should_send is False

    def test_ai_mode_respects_auto_send_flag(self) -> None:
        """AI mode checks the auto_send flag from evaluation."""
        flow = AutonomousFlow(None, None, None, None, None, None, None)  # type: ignore

        # With auto_send=True
        eval_yes = {"decision": "YES", "draft": "Hi!", "auto_send": True}
        assert flow._should_auto_send(eval_yes, "ai", False, 0.5) is True

        # With auto_send=False
        eval_no = {"decision": "YES", "draft": "Hi!", "auto_send": False}
        assert flow._should_auto_send(eval_no, "ai", False, 0.5) is False

        # Missing auto_send defaults to False
        eval_missing = {"decision": "YES", "draft": "Hi!"}
        assert flow._should_auto_send(eval_missing, "ai", False, 0.5) is False

    def test_rubric_mode_uses_threshold(self) -> None:
        """Rubric mode auto-sends when score >= threshold."""
        flow = AutonomousFlow(None, None, None, None, None, None, None)  # type: ignore

        # Score above threshold
        eval_high = {"decision": "YES", "score": 0.8}
        assert flow._should_auto_send(eval_high, "rubric", False, 0.7) is True

        # Score below threshold
        eval_low = {"decision": "YES", "score": 0.6}
        assert flow._should_auto_send(eval_low, "rubric", False, 0.7) is False

        # Score exactly at threshold
        eval_exact = {"decision": "YES", "score": 0.7}
        assert flow._should_auto_send(eval_exact, "rubric", False, 0.7) is True

    def test_hybrid_mode_checks_both(self) -> None:
        """Hybrid mode requires both score and confidence thresholds."""
        flow = AutonomousFlow(None, None, None, None, None, None, None)  # type: ignore

        # Both pass
        eval_pass = {"decision": "YES", "score": 0.8, "confidence": 0.6}
        assert flow._should_auto_send(eval_pass, "hybrid", False, 0.7) is True

        # Score fails
        eval_low_score = {"decision": "YES", "score": 0.6, "confidence": 0.9}
        assert flow._should_auto_send(eval_low_score, "hybrid", False, 0.7) is False

        # Confidence fails
        eval_low_conf = {"decision": "YES", "score": 0.9, "confidence": 0.4}
        assert flow._should_auto_send(eval_low_conf, "hybrid", False, 0.7) is False

    def test_shadow_mode_overrides_all(self) -> None:
        """Shadow mode prevents sending regardless of other conditions."""
        flow = AutonomousFlow(None, None, None, None, None, None, None)  # type: ignore
        perfect_eval = {"decision": "YES", "score": 1.0, "confidence": 1.0, "auto_send": True}

        # Shadow mode blocks all modes
        assert flow._should_auto_send(perfect_eval, "ai", True, 0.0) is False
        assert flow._should_auto_send(perfect_eval, "rubric", True, 0.0) is False
        assert flow._should_auto_send(perfect_eval, "hybrid", True, 0.0) is False

    def test_decision_no_blocks_send(self) -> None:
        """Decision=NO prevents sending in all modes."""
        flow = AutonomousFlow(None, None, None, None, None, None, None)  # type: ignore
        eval_no = {"decision": "NO", "score": 1.0, "auto_send": True}

        assert flow._should_auto_send(eval_no, "ai", False, 0.0) is False
        assert flow._should_auto_send(eval_no, "rubric", False, 0.0) is False
        assert flow._should_auto_send(eval_no, "hybrid", False, 0.0) is False
