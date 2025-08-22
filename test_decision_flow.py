#!/usr/bin/env python3
"""Test the complete decision flow with fixed extraction logic."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from yc_matcher.infrastructure.openai_decision import OpenAIDecisionAdapter
from yc_matcher.domain.entities import Profile, Criteria
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def test_decision_flow():
    """Test the complete decision evaluation flow."""
    print("\n" + "="*60)
    print("TESTING COMPLETE DECISION FLOW")
    print("="*60)
    
    # Create adapter
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    adapter = OpenAIDecisionAdapter(
        client=client,
        model="gpt-5",
        logger=None,
    )
    
    # Create test data
    profile = Profile(
        raw_text="""
        I'm a full-stack engineer with 10 years experience.
        Skills: Python, FastAPI, React, Docker, Kubernetes, AWS.
        Built several successful startups from 0 to 1.
        Looking for an equal equity co-founder.
        Available immediately, based in NYC.
        """
    )
    
    criteria = Criteria(
        text="""
        Looking for a technical co-founder with:
        - Python and FastAPI experience
        - Full-stack capabilities
        - Docker/K8s knowledge
        - Available within 3 months
        - US-based
        - Open to 50/50 equity
        """
    )
    
    print("\nProfile:", profile.raw_text[:100], "...")
    print("Criteria:", criteria.text[:100], "...")
    
    # Test evaluation
    try:
        print("\n🔄 Evaluating profile...")
        result = adapter.evaluate(profile, criteria)
        
        print("\n✅ EVALUATION SUCCESSFUL!")
        print(f"Decision: {result.get('decision')}")
        print(f"Score: {result.get('score')}")
        print(f"Confidence: {result.get('confidence')}")
        print(f"Rationale: {result.get('rationale')}")
        
        if result.get('draft'):
            print(f"\nDraft message:\n{result.get('draft')[:200]}...")
            
        # Check if it's a proper evaluation (not an error)
        if result.get('decision') in ['YES', 'NO']:
            print("\n✅ VALID DECISION RECEIVED")
            return True
        elif result.get('decision') == 'ERROR':
            print(f"\n❌ ERROR DECISION: {result.get('error')}")
            return False
        else:
            print(f"\n❌ UNEXPECTED DECISION: {result.get('decision')}")
            return False
            
    except Exception as e:
        print(f"\n❌ EVALUATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the test."""
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ No OPENAI_API_KEY found")
        return 1
        
    success = test_decision_flow()
    
    if success:
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED - DECISION FLOW WORKING!")
        print("="*60)
        return 0
    else:
        print("\n" + "="*60)
        print("❌ TEST FAILED - DECISION FLOW BROKEN")
        print("="*60)
        return 1


if __name__ == "__main__":
    exit(main())