#!/usr/bin/env python3
"""
Full integration test to verify all fixes are properly integrated.
Tests the complete flow: GPT-5 evaluation → draft generation → message filling → sending
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from yc_matcher.infrastructure.openai_decision import OpenAIDecisionAdapter
from yc_matcher.infrastructure.browser_playwright_async import PlaywrightBrowserAsync
from yc_matcher.infrastructure.jsonl_logger import JSONLLogger
from yc_matcher.domain.entities import Profile, Criteria
from yc_matcher.application.use_cases import EvaluateProfile, SendMessage


def test_gpt5_fallback():
    """Test GPT-5 with proper fallback handling."""
    print("\n" + "="*60)
    print("TEST 1: GPT-5 Response Parsing & Fallback")
    print("="*60)
    
    # Setup logger
    log_path = Path(".runs/test_integration.jsonl")
    log_path.parent.mkdir(exist_ok=True)
    logger = JSONLLogger(log_path)
    
    # Mock OpenAI client
    mock_client = Mock()
    
    # First call will fail with temperature error
    mock_client.responses.create.side_effect = [
        Exception("'temperature' does not support 0.3 with this model"),
        Mock(
            output_text='{"decision": "YES", "rationale": "Strong match", "draft": "Hi Sarah!", "score": 0.85, "confidence": 0.9}',
            usage=Mock(input_tokens=100, output_tokens=50)
        )
    ]
    
    # Create adapter
    adapter = OpenAIDecisionAdapter(mock_client, model="gpt-5", logger=logger)
    
    # Test evaluation
    profile = Profile(raw_text="Sarah Chen, SF, Business background")
    criteria = Criteria(text="Looking for business cofounder in SF")
    
    result = adapter.evaluate(profile, criteria)
    
    # Verify results
    assert result["decision"] == "YES", f"Expected YES, got {result['decision']}"
    assert result["draft"] == "Hi Sarah!", f"Draft not extracted correctly"
    assert result["score"] == 0.85, f"Score not extracted correctly"
    
    # Check logs for fallback
    with open(log_path) as f:
        logs = f.read()
        assert "response_format_fallback" in logs, "Fallback not logged"
    
    print("✅ GPT-5 fallback handling works correctly")
    print(f"   - Decision: {result['decision']}")
    print(f"   - Draft: {result['draft']}")
    print(f"   - Score: {result['score']}")


async def test_browser_selectors():
    """Test browser has correct YC-specific selectors."""
    print("\n" + "="*60)
    print("TEST 2: Browser YC-Specific Selectors")
    print("="*60)
    
    # Create browser instance
    browser = PlaywrightBrowserAsync()
    
    # Test message fill method has correct selector
    import inspect
    fill_source = inspect.getsource(browser.fill_message)
    
    # Check for YC-specific selector
    yc_selector = "excited about potentially working"
    assert yc_selector in fill_source, f"YC selector '{yc_selector}' not found in fill_message"
    
    # Check send button selector
    send_source = inspect.getsource(browser.send)
    invite_button = "Invite to connect"
    assert invite_button in send_source, f"YC button '{invite_button}' not found in send method"
    
    print("✅ Browser has correct YC-specific selectors")
    print(f"   - Message box: textarea[placeholder*='excited about potentially working']")
    print(f"   - Send button: button:has-text('Invite to connect')")


def test_flow_integration():
    """Test the complete flow integration."""
    print("\n" + "="*60)
    print("TEST 3: Complete Flow Integration")
    print("="*60)
    
    # Setup components
    logger = JSONLLogger(Path(".runs/test_integration.jsonl"))
    
    # Mock decision adapter
    mock_decision = Mock()
    mock_decision.evaluate.return_value = {
        "decision": "YES",
        "rationale": "Perfect match",
        "score": 0.9,
        "confidence": 0.95
    }
    
    # Mock message renderer
    mock_message = Mock()
    mock_message.render.return_value = "Hi! I'm excited to connect about your startup."
    
    # Create evaluate use case
    evaluate = EvaluateProfile(
        decision=mock_decision,
        message=mock_message
    )
    
    # Test evaluation
    profile = Profile(raw_text="Test profile")
    criteria = Criteria(text="Test criteria")
    
    result = evaluate(profile, criteria)
    
    # Verify draft is included
    assert "draft" in result, "Draft not added to evaluation result"
    assert result["draft"] == "Hi! I'm excited to connect about your startup."
    assert result["decision"] == "YES"
    
    print("✅ Flow correctly integrates evaluation and draft generation")
    print(f"   - Decision: {result['decision']}")
    print(f"   - Draft: {result['draft'][:50]}...")
    
    # Test send use case
    mock_browser = Mock()
    mock_browser.focus_message_box = Mock()
    mock_browser.fill_message = Mock()
    mock_browser.send = Mock()
    mock_browser.verify_sent = Mock(return_value=True)
    
    mock_quota = Mock()
    mock_quota.check_and_increment = Mock(return_value=True)
    
    send = SendMessage(
        quota=mock_quota,
        browser=mock_browser,
        logger=logger
    )
    
    # Test sending
    success = send(result["draft"], limit=1)
    
    # Verify browser methods were called in correct order
    assert mock_browser.focus_message_box.called, "focus_message_box not called"
    assert mock_browser.fill_message.called, "fill_message not called"
    assert mock_browser.send.called, "send not called"
    
    # Verify draft was passed correctly
    mock_browser.fill_message.assert_called_with("Hi! I'm excited to connect about your startup.")
    
    print("✅ Send use case correctly calls browser methods")
    print(f"   - focus_message_box: Called")
    print(f"   - fill_message: Called with draft")
    print(f"   - send: Called")
    print(f"   - verify_sent: Returned {success}")


def test_autonomous_flow():
    """Test autonomous flow passes draft correctly."""
    print("\n" + "="*60)
    print("TEST 4: Autonomous Flow Draft Passing")
    print("="*60)
    
    # Check autonomous_flow.py has correct implementation
    from yc_matcher.application.autonomous_flow import AutonomousFlow
    import inspect
    
    flow_source = inspect.getsource(AutonomousFlow.run)
    
    # Check key lines are present
    assert "evaluation = self.evaluate(profile, criteria_obj)" in flow_source
    assert 'draft = evaluation.get("draft", "")' in flow_source
    assert "success = self.send(draft, 1)" in flow_source
    
    print("✅ Autonomous flow correctly extracts and passes draft")
    print("   - Calls evaluate() to get decision and draft")
    print("   - Extracts draft from evaluation result")
    print("   - Passes draft to send() method")


def main():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("COMPREHENSIVE INTEGRATION TEST")
    print("Verifying all fixes are properly integrated")
    print("="*60)
    
    try:
        # Test 1: GPT-5 fallback
        test_gpt5_fallback()
        
        # Test 2: Browser selectors
        asyncio.run(test_browser_selectors())
        
        # Test 3: Flow integration
        test_flow_integration()
        
        # Test 4: Autonomous flow
        test_autonomous_flow()
        
        print("\n" + "="*60)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("="*60)
        print("\nThe complete flow is properly integrated:")
        print("1. GPT-5 evaluation with fallback handling ✓")
        print("2. YC-specific browser selectors ✓")
        print("3. Draft generation and passing ✓")
        print("4. Message filling and sending ✓")
        print("\nThe bot should now successfully:")
        print("• Evaluate profiles using GPT-5 (or gpt-4o fallback)")
        print("• Generate personalized drafts")
        print("• Fill the YC message box correctly")
        print("• Click the 'Invite to connect' button")
        print("• Send messages to qualified candidates")
        
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