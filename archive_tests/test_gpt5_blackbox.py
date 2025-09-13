#!/usr/bin/env python3
"""
TEST THE GPT-5 BLACK BOX
Shows exactly what goes IN and what comes OUT of GPT-5
"""

import json
import os
import sys
from pathlib import Path

# Load .env file properly
env_file = Path(".env")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                if "#" in value:
                    value = value.split("#")[0].strip()
                if key not in os.environ:
                    os.environ[key] = value

sys.path.insert(0, "src")


def test_gpt5_decision():
    """Test the GPT-5 decision making with REAL profile."""
    print("\n" + "=" * 60)
    print("GPT-5 BLACK BOX TEST")
    print("=" * 60)

    from openai import OpenAI

    from yc_matcher.domain.entities import Criteria, Profile
    from yc_matcher.infrastructure.ai.openai_decision import OpenAIDecisionAdapter

    # ========================================
    # YOUR PROFILE (who you are)
    # ========================================
    YOUR_PROFILE = """
    I'm JJ, a technical founder with 10+ years experience in AI/ML and full-stack development.
    Built and sold 2 startups in edtech and healthtech.
    Strong engineering background, expert in Python, React, cloud architecture.
    Located in San Francisco Bay Area.
    Looking for a business co-founder to build the next unicorn.
    """

    # ========================================
    # YOUR CRITERIA (what you're looking for)
    # ========================================
    MATCH_CRITERIA = """
    Looking for a business/sales co-founder with:
    - Strong business development and sales experience
    - Previous startup experience (ideally as founder)
    - Located in SF Bay Area or willing to relocate
    - Domain expertise in AI, education, or healthcare
    - Available full-time within 3 months
    - Complementary skills (I handle tech, they handle business)
    """

    # ========================================
    # MESSAGE TEMPLATE (output format)
    # ========================================
    MESSAGE_TEMPLATE = """
    When writing a message, follow this template:

    Hi [Name]!

    I noticed your [specific experience/background from their profile].

    I'm a technical founder with [relevant experience]. Currently exploring
    [relevant domain] and looking for a business co-founder.

    [One specific thing about why they're a good match based on their profile]

    Would love to connect and explore potential collaboration!

    Best,
    JJ
    """

    # ========================================
    # CANDIDATE PROFILE (Dr. Juan Rosario from SCREEN_FOUR)
    # ========================================
    CANDIDATE_PROFILE = """
    Name: Dr. Juan Rosario Jr.
    Location: Rhode Island, USA
    Age: 34
    Last seen: 4 days ago

    I'm technical, passively looking, and could help a co-founder with their existing idea or
    explore new ideas together.

    I'm willing to do Operations and Sales and marketing.

    About Me:
    Dr. Juan E. Rosario Jr. is a bilingual (English & Spanish) healthcare provider, 2x founder,
    and personal development coach whose mission is to empower individuals and organizations
    through coaching. He is passionate about helping others realize their full potential and
    overcome doubt to achieve a much more fulfilling and balanced life. Dr. Rosario provides
    dynamic planning solutions for those preparing to enter the healthcare job market.
    His expertise extends to working with leading healthcare organizations that are invested
    in positively impacting society. Dr. Rosario is a true master in building relationships
    and delivering current strategies that elevate all members of organizations.

    Free Time: Travel, gym, coffee, family time

    Background:
    - Founder and Director of Myelinated Solutions (boutique coaching practice)
    - Founder and President of Latino y Sano! (International BiPOC psychoeducational nonprofit)
    - Education: 2024- Doctorate in Clinical Neuropsychology, 2016 B.A. Justice Studies
    - Employment: Hospital and Private practice (mental health settings)

    What I'm looking for:
    - Co-founder in my country (United States)
    - Ideally aligned with my interests

    Interests: Health/Wellness, Healthcare, Non-Profit
    """

    # ========================================
    # SEND TO GPT-5
    # ========================================
    print("\n1. PREPARING INPUT FOR GPT-5")
    print("-" * 40)

    # Combine everything into the criteria that goes to GPT-5
    full_criteria = f"""
{YOUR_PROFILE}

{MATCH_CRITERIA}

{MESSAGE_TEMPLATE}
"""

    print(f"Your Profile: {len(YOUR_PROFILE)} chars")
    print(f"Match Criteria: {len(MATCH_CRITERIA)} chars")
    print(f"Message Template: {len(MESSAGE_TEMPLATE)} chars")
    print(f"Candidate Profile: {len(CANDIDATE_PROFILE)} chars")

    # Create entities
    profile = Profile(raw_text=CANDIDATE_PROFILE)
    criteria = Criteria(text=full_criteria)

    # Initialize OpenAI with GPT-5
    client = OpenAI()
    model = os.getenv("OPENAI_DECISION_MODEL", "gpt-5")
    print(f"\nUsing model: {model}")

    # Create adapter
    from yc_matcher.infrastructure.logging.jsonl_logger import JSONLLogger

    logger = JSONLLogger(Path(".runs/gpt5_test.jsonl"))
    adapter = OpenAIDecisionAdapter(client, logger=logger)

    # ========================================
    # CALL GPT-5
    # ========================================
    print("\n2. CALLING GPT-5...")
    print("-" * 40)

    import time

    start = time.time()

    try:
        # For debugging, let's see the raw response
        import logging

        logging.basicConfig(level=logging.DEBUG)

        result = adapter.evaluate(profile, criteria)
        latency_ms = int((time.time() - start) * 1000)

        print(f"✅ Response received in {latency_ms}ms")

        # ========================================
        # SHOW OUTPUT
        # ========================================
        print("\n3. GPT-5 OUTPUT")
        print("-" * 40)

        print(f"\n📊 DECISION: {result.get('decision')}")
        print(f"\n📝 REASONING:\n{result.get('rationale')}")
        print(f"\n⭐ SCORE: {result.get('score')}")
        print(f"\n🎯 CONFIDENCE: {result.get('confidence', 'N/A')}")

        if result.get("decision") == "YES":
            print("\n💬 PERSONALIZED MESSAGE:")
            print("-" * 40)
            print(result.get("draft", "No message generated"))
        else:
            print("\n❌ No message (decision was NO)")

        # Save full response
        output_file = Path("gpt5_response.json")
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n✅ Full response saved to: {output_file}")

    except Exception as e:
        print(f"\n❌ Error calling GPT-5: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_gpt5_decision()
