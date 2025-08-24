#!/usr/bin/env python3
"""Test script to verify Context7-based GPT-5 implementation."""

import json
import os
from unittest.mock import Mock, MagicMock
from types import SimpleNamespace

# Set up test environment
os.environ["GPT5_MAX_TOKENS"] = "4000"
os.environ["GPT5_TEMPERATURE"] = "0.7"
os.environ["GPT5_VERBOSITY"] = "low"
os.environ["GPT5_REASONING_EFFORT"] = "minimal"

from yc_matcher import config
from yc_matcher.infrastructure.ai.openai_decision import OpenAIDecisionAdapter
from yc_matcher.domain.entities import Profile, Criteria


def test_gpt5_with_context7_params():
    """Test that GPT-5 calls use Context7-verified parameters."""
    print("\n=== Testing GPT-5 with Context7 Parameters ===\n")
    
    # Create mock client
    mock_client = Mock()
    mock_client.responses = Mock()
    
    # Mock the response
    mock_response = SimpleNamespace(
        output_text='{"decision": "YES", "rationale": "Great match!", "draft": "Hi!", "score": 0.9, "confidence": 0.95}',
        usage=SimpleNamespace(input_tokens=100, output_tokens=50)
    )
    
    # Track what params are sent
    actual_params = {}
    
    def capture_params(**kwargs):
        actual_params.update(kwargs)
        return mock_response
    
    mock_client.responses.create = Mock(side_effect=capture_params)
    
    # Create adapter
    adapter = OpenAIDecisionAdapter(client=mock_client, model="gpt-5")
    
    # Test evaluate
    profile = Profile(raw_text="Experienced Python developer")
    criteria = Criteria(text="Looking for Python developers")
    
    result = adapter.evaluate(profile, criteria)
    
    # Verify Context7 parameters were used
    print("Parameters sent to API:")
    print(f"  model: {actual_params.get('model')}")
    print(f"  max_output_tokens: {actual_params.get('max_output_tokens')}")
    print(f"  temperature: {actual_params.get('temperature')}")
    print(f"  text object: {actual_params.get('text')}")
    print(f"  reasoning object: {actual_params.get('reasoning')}")
    
    # Assertions based on Context7 truth
    assert actual_params.get('model') == 'gpt-5', "Wrong model"
    assert actual_params.get('max_output_tokens') == 4000, "Should use 4000 tokens"
    assert actual_params.get('temperature') == 0.7, "Wrong temperature"
    
    # CRITICAL: Verify nested structure per Context7
    assert 'text' in actual_params, "Missing text object!"
    assert actual_params['text'].get('verbosity') == 'low', "Verbosity not nested in text!"
    
    assert 'reasoning' in actual_params, "Missing reasoning object!"
    assert actual_params['reasoning'].get('effort') == 'minimal', "Reasoning effort not set!"
    
    print("\n✅ SUCCESS: All Context7 parameters correctly applied!")
    print(f"   Decision: {result.get('decision')}")
    print(f"   Score: {result.get('score')}")
    
    return True


def test_fallback_behavior():
    """Test that unsupported params are removed on error."""
    print("\n=== Testing Fallback Behavior ===\n")
    
    # Create mock client that fails first time
    mock_client = Mock()
    mock_client.responses = Mock()
    
    call_count = 0
    first_params = {}
    second_params = {}
    
    def mock_create(**kwargs):
        nonlocal call_count, first_params, second_params
        call_count += 1
        
        if call_count == 1:
            first_params.update(kwargs)
            # Simulate SDK error for unsupported params
            raise Exception("Unsupported parameter: text")
        else:
            second_params.update(kwargs)
            return SimpleNamespace(
                output_text='{"decision": "NO", "rationale": "Not a match", "draft": "", "score": 0.3, "confidence": 0.8}',
                usage=SimpleNamespace(input_tokens=100, output_tokens=50)
            )
    
    mock_client.responses.create = Mock(side_effect=mock_create)
    
    # Create adapter with logger to see fallback
    mock_logger = Mock()
    adapter = OpenAIDecisionAdapter(client=mock_client, model="gpt-5", logger=mock_logger)
    
    # Test evaluate
    profile = Profile(raw_text="Java developer")
    criteria = Criteria(text="Looking for Python developers")
    
    result = adapter.evaluate(profile, criteria)
    
    print("First attempt params:")
    print(f"  Had text object: {'text' in first_params}")
    print(f"  Had reasoning object: {'reasoning' in first_params}")
    
    print("\nSecond attempt params (after fallback):")
    print(f"  Had text object: {'text' in second_params}")
    print(f"  Had reasoning object: {'reasoning' in second_params}")
    
    # Verify fallback worked
    assert 'text' in first_params, "Should try with text first"
    assert 'text' not in second_params, "Should remove text on retry"
    assert 'reasoning' not in second_params, "Should remove reasoning on retry"
    
    print("\n✅ SUCCESS: Fallback correctly removes unsupported params!")
    
    return True


def test_config_integration():
    """Test that config values are properly loaded."""
    print("\n=== Testing Config Integration ===\n")
    
    print("Configuration values:")
    print(f"  GPT5_MAX_TOKENS: {config.get_gpt5_max_tokens()}")
    print(f"  GPT5_TEMPERATURE: {config.get_gpt5_temperature()}")
    print(f"  GPT5_TOP_P: {config.get_gpt5_top_p()}")
    print(f"  GPT5_VERBOSITY: {config.get_gpt5_verbosity()}")
    print(f"  GPT5_REASONING_EFFORT: {config.get_gpt5_reasoning_effort()}")
    
    assert config.get_gpt5_max_tokens() == 4000, "Wrong max tokens"
    assert config.get_gpt5_temperature() == 0.7, "Wrong temperature"
    assert config.get_gpt5_verbosity() == "low", "Wrong verbosity"
    assert config.get_gpt5_reasoning_effort() == "minimal", "Wrong reasoning effort"
    
    print("\n✅ SUCCESS: Config properly loads Context7 parameters!")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Context7-based GPT-5 Implementation")
    print("=" * 60)
    
    try:
        test_config_integration()
        test_gpt5_with_context7_params()
        test_fallback_behavior()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("The codebase now correctly implements Context7 documentation.")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        exit(1)