#!/usr/bin/env python
"""Test the decision engine with GPT-5-thinking model."""

import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up environment
os.environ["ENABLE_OPENAI"] = "1"
os.environ["DECISION_MODE"] = "hybrid"
os.environ["OPENAI_DECISION_MODEL"] = "gpt-5-thinking"  # GPT-5-THINKING ONLY!

from openai import OpenAI

from src.yc_matcher.domain.entities import Criteria, Profile
from src.yc_matcher.infrastructure.openai_decision import OpenAIDecisionAdapter


def test_decision_with_message_generation():
    """Test that GPT-5-thinking generates actual message drafts."""

    print("\n🤖 Testing GPT-5-THINKING Decision Engine (NO GPT-4 EVER!)...")
    print(f"Model: {os.getenv('OPENAI_DECISION_MODEL')}")

    # Create OpenAI client
    client = OpenAI()

    # Create decision adapter
    decision = OpenAIDecisionAdapter(
        client=client,
        model="gpt-5-thinking",  # GPT-5-THINKING ONLY!
    )

    # Test profile (example)
    profile_text = """
    Name: John Smith
    Location: San Francisco, CA
    Background: Full-stack engineer with 5 years experience at Google.
    Built ML infrastructure for YouTube recommendations.
    Passionate about developer tools and AI applications.
    Skills: Python, FastAPI, React, TypeScript, PostgreSQL, Docker, Kubernetes
    Looking for: Technical co-founder to build AI-powered dev tools startup
    """

    # Test criteria and template
    criteria_text = """
    Looking for: Technical co-founder with backend expertise
    Required Skills: Python, FastAPI, database design
    Nice to have: ML/AI experience, big tech background
    Location: San Francisco or remote

    Message Template:
    Hey [Name],

    I noticed your experience with [specific skill/project] - that's exactly the kind of expertise I'm looking for.
    I'm building [your startup idea] and your background in [relevant experience] would be perfect.

    Would love to chat about potentially partnering up. Are you free for a quick call this week?

    Best,
    JJ
    """

    # Create entities
    profile = Profile(raw_text=profile_text)
    criteria = Criteria(text=criteria_text)

    # Evaluate
    print("\n📝 Evaluating profile...")
    result = decision.evaluate(profile, criteria)

    # Display results
    print("\n✅ RESULTS:")
    print(f"Decision: {result.get('decision')}")
    print(f"Score: {result.get('score', 0):.2f}")
    print(f"Confidence: {result.get('confidence', 0):.2f}")
    print(f"Rationale: {result.get('rationale')}")

    if result.get("draft"):
        print(f"\n💬 Generated Message:\n{'-' * 50}")
        print(result.get("draft"))
        print(f"{'-' * 50}")
    else:
        print("\n⚠️ No message draft generated")

    # Check if it actually worked
    if result.get("decision") == "YES" and result.get("draft"):
        print("\n🎉 SUCCESS! GPT-5-thinking is generating personalized messages!")
        return True
    else:
        print("\n❌ ISSUE: Decision engine not generating messages properly")
        return False


if __name__ == "__main__":
    success = test_decision_with_message_generation()
    exit(0 if success else 1)
