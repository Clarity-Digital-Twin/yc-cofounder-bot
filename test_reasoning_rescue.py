#!/usr/bin/env python3
"""
Test that our reasoning-only rescue actually works.
This simulates REAL GPT-5 behavior where it returns ONLY reasoning items.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from yc_matcher.infrastructure.openai_decision import OpenAIDecisionAdapter
from yc_matcher.infrastructure.jsonl_logger import JSONLLogger
from yc_matcher.domain.entities import Profile, Criteria


def test_reasoning_only_rescue():
    """Test that we can extract JSON from reasoning-only responses."""
    print("\n" + "="*60)
    print("TESTING REASONING-ONLY RESCUE")
    print("="*60)
    
    # Create a REALISTIC mock that matches actual GPT-5 behavior
    def mock_reasoning_only_response():
        """This is what GPT-5 ACTUALLY returns sometimes."""
        return Mock(
            output=[
                Mock(
                    type="reasoning",
                    content=(
                        "Let me analyze this profile. The candidate has strong technical skills "
                        "and matches the criteria well. I'll provide my evaluation:\n\n"
                        '{"decision": "YES", "rationale": "Strong full-stack engineer with '
                        'Python and React experience", "draft": "Hi! Your experience building '
                        'scalable systems caught my attention.", "score": 0.85, "confidence": 0.9}'
                    )
                )
            ],
            output_text="",  # Empty or None - this is the problem!
            usage=Mock(input_tokens=100, output_tokens=150)
        )
    
    # Setup
    log_path = Path(".runs/test_reasoning_rescue.jsonl")
    log_path.parent.mkdir(exist_ok=True)
    logger = JSONLLogger(log_path)
    
    mock_client = Mock()
    
    # First call with verbosity will still return reasoning-only
    # Second call without verbosity will also return reasoning-only
    mock_client.responses.create.side_effect = [
        Exception("'verbosity' is not a valid parameter"),  # First attempt fails
        mock_reasoning_only_response()  # Retry without verbosity
    ]
    
    # Create adapter
    adapter = OpenAIDecisionAdapter(mock_client, model="gpt-5", logger=logger)
    
    # Test evaluation
    profile = Profile(raw_text="Full-stack engineer, Python, React, AWS experience")
    criteria = Criteria(text="Looking for technical co-founder")
    
    print("Testing with reasoning-only response...")
    result = adapter.evaluate(profile, criteria)
    
    # Verify the rescue worked
    assert result["decision"] == "YES", f"Expected YES, got {result['decision']}"
    assert "Strong full-stack" in result["rationale"]
    assert "Your experience" in result["draft"]
    assert result["score"] == 0.85
    
    print("✅ Successfully rescued JSON from reasoning item!")
    print(f"   - Decision: {result['decision']}")
    print(f"   - Score: {result['score']}")
    print(f"   - Draft extracted: {len(result['draft'])} chars")
    
    # Check logs for rescue event
    with open(log_path) as f:
        logs = f.read()
        assert "gpt5_reasoning_rescue" in logs, "Rescue event not logged"
        assert '"success": true' in logs.lower(), "Rescue not marked as success"
    
    print("✅ Reasoning rescue properly logged")
    
    return True


def test_no_json_in_reasoning():
    """Test handling when reasoning has no valid JSON."""
    print("\n" + "="*60)
    print("TESTING NO JSON IN REASONING")
    print("="*60)
    
    # Mock response with reasoning but no JSON
    mock_response = Mock(
        output=[
            Mock(
                type="reasoning",
                content="This profile doesn't match. I won't provide a recommendation."
            )
        ],
        output_text="",
        usage=Mock(input_tokens=100, output_tokens=50)
    )
    
    mock_client = Mock()
    mock_client.responses.create.return_value = mock_response
    
    adapter = OpenAIDecisionAdapter(mock_client, model="gpt-5")
    profile = Profile(raw_text="Test")
    criteria = Criteria(text="Test")
    
    print("Testing with reasoning but no JSON...")
    
    # Should return ERROR decision instead of crashing
    result = adapter.evaluate(profile, criteria)
    
    assert result["decision"] == "ERROR"
    assert "Could not extract" in result["rationale"]
    
    print("✅ Correctly handled reasoning with no JSON")
    print(f"   - Decision: {result['decision']}")
    print(f"   - Error handled gracefully")
    
    return True


def test_mixed_output_types():
    """Test when GPT-5 returns both reasoning AND message items."""
    print("\n" + "="*60)
    print("TESTING MIXED OUTPUT TYPES")
    print("="*60)
    
    # Mock response with BOTH types
    mock_response = Mock(
        output=[
            Mock(
                type="reasoning",
                content="Analyzing the profile..."
            ),
            Mock(
                type="message",
                content=[
                    Mock(
                        text='{"decision": "NO", "rationale": "Not a match", '
                             '"draft": "", "score": 0.2, "confidence": 0.8}'
                    )
                ]
            )
        ],
        output_text='{"decision": "NO", "rationale": "Not a match", "draft": "", "score": 0.2, "confidence": 0.8}',
        usage=Mock(input_tokens=100, output_tokens=100)
    )
    
    mock_client = Mock()
    mock_client.responses.create.return_value = mock_response
    
    adapter = OpenAIDecisionAdapter(mock_client, model="gpt-5")
    profile = Profile(raw_text="Designer")
    criteria = Criteria(text="Need engineer")
    
    print("Testing with both reasoning and message items...")
    
    result = adapter.evaluate(profile, criteria)
    
    # Should use message item, not need rescue
    assert result["decision"] == "NO"
    assert result["score"] == 0.2
    
    print("✅ Correctly used message item when available")
    print(f"   - Decision: {result['decision']}")
    print(f"   - No rescue needed")
    
    return True


def main():
    """Run all reasoning rescue tests."""
    try:
        test_reasoning_only_rescue()
        test_no_json_in_reasoning()
        test_mixed_output_types()
        
        print("\n" + "="*60)
        print("✅ ALL REASONING RESCUE TESTS PASSED!")
        print("="*60)
        print("\nThe fix successfully handles:")
        print("1. Reasoning-only responses (extracts JSON from reasoning)")
        print("2. No JSON in reasoning (returns ERROR decision)")
        print("3. Mixed output types (prefers message items)")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()