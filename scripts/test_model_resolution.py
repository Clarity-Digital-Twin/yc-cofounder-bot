#!/usr/bin/env python
"""Test the model resolution system.

This verifies that:
1. Models are discovered from OpenAI API
2. Best available model is selected
3. Environment variables are set correctly
4. Adapters use resolved models
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_model_resolution():
    """Test model discovery and resolution."""

    print("\n🔍 Testing Model Resolution System...")
    print("=" * 60)

    # Clear any existing resolved models to test fresh
    os.environ.pop("DECISION_MODEL_RESOLVED", None)
    os.environ.pop("CUA_MODEL_RESOLVED", None)

    # Import and run resolver
    from yc_matcher.infrastructure.ai.model_resolver import resolve_and_set_models

    print("\n1️⃣ Running model discovery...")
    try:
        result = resolve_and_set_models()
        print("   ✅ Discovery successful!")
        print(f"   Decision Model: {result['decision_model']}")
        print(f"   CUA Model: {result['cua_model'] or 'Not available'}")
    except Exception as e:
        print(f"   ❌ Discovery failed: {e}")
        return False

    # Verify environment variables were set
    print("\n2️⃣ Verifying environment variables...")
    decision_resolved = os.getenv("DECISION_MODEL_RESOLVED")
    cua_resolved = os.getenv("CUA_MODEL_RESOLVED")

    if decision_resolved:
        print(f"   ✅ DECISION_MODEL_RESOLVED = {decision_resolved}")
    else:
        print("   ❌ DECISION_MODEL_RESOLVED not set")
        return False

    if cua_resolved:
        print(f"   ✅ CUA_MODEL_RESOLVED = {cua_resolved}")
    else:
        print("   ⚠️ CUA_MODEL_RESOLVED not set (may not have access)")

    # Test decision adapter uses resolved model
    print("\n3️⃣ Testing Decision Adapter...")
    from openai import OpenAI
    from yc_matcher.infrastructure.ai.openai_decision import OpenAIDecisionAdapter

    client = OpenAI()
    adapter = OpenAIDecisionAdapter(client=client)

    if adapter.model == decision_resolved:
        print(f"   ✅ Decision adapter using resolved model: {adapter.model}")
    else:
        print("   ❌ Decision adapter not using resolved model")
        print(f"      Expected: {decision_resolved}")
        print(f"      Got: {adapter.model}")
        return False

    # Test CUA adapter if available
    if cua_resolved:
        print("\n4️⃣ Testing CUA Adapter...")
        try:
            from yc_matcher.infrastructure.browser.openai_cua import OpenAICUABrowser

            cua = OpenAICUABrowser()

            if cua.model == cua_resolved:
                print(f"   ✅ CUA adapter using resolved model: {cua.model}")
            else:
                print("   ❌ CUA adapter not using resolved model")
                print(f"      Expected: {cua_resolved}")
                print(f"      Got: {cua.model}")
                return False
        except Exception as e:
            print(f"   ⚠️ Could not test CUA adapter: {e}")

    # Test fallback behavior
    print("\n5️⃣ Testing fallback chain...")

    # Check what type of model we got
    if "gpt-5" in decision_resolved.lower():
        if "thinking" in decision_resolved.lower():
            print("   ✅ Got preferred GPT-5 thinking model!")
        else:
            print("   ✅ Got GPT-5 model (non-thinking variant)")
    elif "gpt-4" in decision_resolved.lower():
        print("   ⚠️ Using GPT-4 fallback (no GPT-5 available on this account)")
    else:
        print(f"   ⚠️ Using unexpected model: {decision_resolved}")

    print("\n" + "=" * 60)
    print("✅ Model Resolution System Working!")
    print("\nSummary:")
    print(f"  • Decision Model: {decision_resolved}")
    print(f"  • CUA Model: {cua_resolved or 'Not available'}")
    print(f"  • Fallback Used: {'Yes' if 'gpt-4' in decision_resolved.lower() else 'No'}")

    return True


if __name__ == "__main__":
    success = test_model_resolution()
    sys.exit(0 if success else 1)
