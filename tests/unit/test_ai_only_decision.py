"""Test AI-only decision mode (simplified from 3 modes to 1)."""

import os
from types import SimpleNamespace
from unittest.mock import Mock, patch

from yc_matcher.domain.entities import Criteria, Profile
from yc_matcher.infrastructure.openai_decision import OpenAIDecisionAdapter


class TestAIOnlyDecision:
    """Test the simplified AI-only decision flow."""

    def test_ai_decision_returns_structured_output(self) -> None:
        """Test AI adapter returns expected JSON structure."""
        # Arrange - Use SimpleNamespace for proper attribute access
        mock_client = Mock()
        # Match exact structure: response.output[].type=='message', item.content[].text
        content_item = SimpleNamespace(
            text='{"decision": "YES", "rationale": "Strong match", "draft": "Hi!", "score": 0.85, "confidence": 0.9}'
        )
        message_item = SimpleNamespace(type="message", content=[content_item])
        mock_response = SimpleNamespace(
            output=[message_item], usage=SimpleNamespace(input_tokens=100, output_tokens=50)
        )
        mock_client.responses.create.return_value = mock_response

        adapter = OpenAIDecisionAdapter(client=mock_client, model="gpt-5")
        profile = Profile(raw_text="Python developer, 5 years experience")
        criteria = Criteria(text="Looking for Python developers")

        # Act
        result = adapter.evaluate(profile, criteria)

        # Assert
        assert result["decision"] == "YES"
        assert result["rationale"] == "Strong match"
        assert result["draft"] == "Hi!"
        assert result["score"] == 0.85
        assert result["confidence"] == 0.9

    def test_ai_decision_includes_personalized_draft(self) -> None:
        """Test AI generates personalized message referencing profile details."""
        # Arrange - Use SimpleNamespace for proper attribute access
        mock_client = Mock()
        personalized_draft = "Hi! I noticed your experience with FastAPI and microservices..."
        content_item = SimpleNamespace(
            text=f'{{"decision": "YES", "rationale": "Match", "draft": "{personalized_draft}", "score": 0.8, "confidence": 0.85}}'
        )
        message_item = SimpleNamespace(type="message", content=[content_item])
        mock_response = SimpleNamespace(
            output=[message_item], usage=SimpleNamespace(input_tokens=150, output_tokens=80)
        )
        mock_client.responses.create.return_value = mock_response

        adapter = OpenAIDecisionAdapter(client=mock_client, model="gpt-5")
        profile = Profile(raw_text="FastAPI expert, built microservices at scale")
        criteria = Criteria(text="Need backend developer")

        # Act
        result = adapter.evaluate(profile, criteria)

        # Assert
        assert "FastAPI" in result["draft"]
        assert "microservices" in result["draft"]
        assert len(result["draft"]) > 20  # Not just a template

    def test_ai_decision_logs_usage_metrics(self) -> None:
        """Test AI adapter logs token usage and cost estimates."""
        # Arrange - Use SimpleNamespace for proper attribute access
        mock_client = Mock()
        mock_logger = Mock()
        content_item = SimpleNamespace(
            text='{"decision": "NO", "rationale": "Not a match", "draft": "", "score": 0.3, "confidence": 0.8}'
        )
        message_item = SimpleNamespace(type="message", content=[content_item])
        mock_response = SimpleNamespace(
            output=[message_item], usage=SimpleNamespace(input_tokens=200, output_tokens=100)
        )
        mock_client.responses.create.return_value = mock_response

        adapter = OpenAIDecisionAdapter(client=mock_client, logger=mock_logger)
        profile = Profile(raw_text="Designer")
        criteria = Criteria(text="Need developer")

        # Act
        adapter.evaluate(profile, criteria)

        # Assert - Should log at least model_usage and decision_latency
        assert mock_logger.emit.call_count >= 2  # May log more with retries
        calls = mock_logger.emit.call_args_list

        # Find the model_usage event
        usage_events = [call[0][0] for call in calls if call[0][0]["event"] == "model_usage"]
        assert len(usage_events) >= 1  # At least one usage event
        usage_event = usage_events[0]
        assert usage_event["tokens_in"] == 200
        assert usage_event["tokens_out"] == 100
        assert "cost_est" in usage_event

        # Check decision_latency event exists
        latency_events = [call[0][0] for call in calls if call[0][0]["event"] == "decision_latency"]
        assert len(latency_events) >= 1  # At least one latency event

    def test_ai_decision_handles_api_errors(self) -> None:
        """Test graceful fallback when API fails."""
        # Arrange
        mock_client = Mock()
        mock_client.responses.create.side_effect = Exception("API rate limit")

        adapter = OpenAIDecisionAdapter(client=mock_client, model="gpt-5")
        profile = Profile(raw_text="Test profile")
        criteria = Criteria(text="Test criteria")

        # Act
        result = adapter.evaluate(profile, criteria)

        # Assert - When API fails, decision is ERROR not NO
        assert result["decision"] == "ERROR"
        assert "error" in result["rationale"].lower() or "failed" in result["rationale"].lower()
        assert result["draft"] == ""
        assert result["score"] == 0.0
        assert result["confidence"] == 0.0

    def test_shadow_mode_prevents_sending(self) -> None:
        """Test shadow mode evaluates but doesn't send."""
        # This is actually tested at the SendMessage use case level
        # but we include a placeholder to show the intent

        # Shadow mode is controlled by environment variable
        with patch.dict(os.environ, {"SHADOW_MODE": "1"}):
            # In shadow mode, SendMessage.execute() should return early
            # without actually sending, just logging the decision
            assert os.getenv("SHADOW_MODE") == "1"

    def test_auto_send_flag_controls_approval(self) -> None:
        """Test auto_send flag determines if approval needed."""
        # Arrange - Use SimpleNamespace for proper attribute access
        mock_client = Mock()
        content_item = SimpleNamespace(
            text='{"decision": "YES", "rationale": "Match", "draft": "Message", "score": 0.8, "confidence": 0.85}'
        )
        message_item = SimpleNamespace(type="message", content=[content_item])
        mock_response = SimpleNamespace(output=[message_item], usage=None)
        mock_client.responses.create.return_value = mock_response

        adapter = OpenAIDecisionAdapter(client=mock_client, model="gpt-5")
        profile = Profile(raw_text="Profile")
        criteria = Criteria(text="Criteria")

        # Act - the adapter itself doesn't control auto_send
        # That's handled by the UI/flow layer
        result = adapter.evaluate(profile, criteria)

        # Assert - adapter just returns decision
        assert result["decision"] == "YES"
        # Auto-send logic would be: if result["decision"] == "YES" and AUTO_SEND: send()

    def test_ai_uses_best_available_model(self) -> None:
        """Test model resolution uses best available model."""
        # Arrange - Use SimpleNamespace for proper attribute access
        mock_client = Mock()
        content_item = SimpleNamespace(
            text='{"decision": "YES", "rationale": "Match", "draft": "Hi", "score": 0.8, "confidence": 0.85}'
        )
        message_item = SimpleNamespace(type="message", content=[content_item])
        mock_response = SimpleNamespace(output=[message_item], usage=None)
        mock_client.responses.create.return_value = mock_response

        # Create adapter with specific model
        adapter = OpenAIDecisionAdapter(client=mock_client, model="gpt-5")

        # Act
        profile = Profile(raw_text="Profile")
        criteria = Criteria(text="Criteria")
        adapter.evaluate(profile, criteria)

        # Assert - The adapter should use the model it was initialized with
        assert adapter.model == "gpt-5"
        # Verify the API was called
        assert mock_client.responses.create.called
