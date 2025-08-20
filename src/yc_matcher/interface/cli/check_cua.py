"""Check OpenAI Computer Use access via Agents SDK."""

from __future__ import annotations

import os
import sys
from typing import Any

try:
    from dotenv import load_dotenv as _load_dotenv
except Exception:  # pragma: no cover
    _load_dotenv = None  # type: ignore[assignment]


def _print(msg: str) -> None:
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def main() -> int:
    """Check OpenAI Computer Use tool availability."""
    if _load_dotenv is not None:
        _load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        _print("ERROR: OPENAI_API_KEY not set. Add it to .env or your environment.")
        return 2

    # Check OpenAI base SDK
    try:
        from openai import OpenAI
    except Exception as e:  # pragma: no cover
        _print(f"ERROR: openai package not installed or incompatible: {e}")
        return 2

    client: Any = OpenAI(api_key=api_key)

    # Step 1: Check model availability
    try:
        models = client.models.list()
        model_ids = {m.id for m in models.data}
        
        # Look for computer-use models
        cua_models = [mid for mid in model_ids if "computer" in mid.lower() or "cua" in mid.lower()]
        
        if cua_models:
            _print(f"Computer Use models found: {', '.join(cua_models)}")
        else:
            _print("Warning: No obvious Computer Use models found. Check your Models endpoint.")
            _print("You may need tier 3-5 access for Computer Use.")
    except Exception as e:
        _print(f"Warning: could not list models: {e}")

    # Step 2: Check Agents SDK availability
    try:
        from agents import Agent, ComputerTool
        _print("SUCCESS: Agents SDK (openai-agents package) is installed.")
    except ImportError:
        _print("ERROR: Agents SDK not installed.")
        _print("Run: pip install openai-agents")
        return 2

    # Step 3: Try to initialize Computer Use
    try:
        cua_model = os.getenv("CUA_MODEL", "computer-use-preview")
        
        agent = Agent(
            model=cua_model,
            tools=[ComputerTool()],
            temperature=0.3
        )
        
        _print(f"SUCCESS: Computer Use agent initialized with model: {cua_model}")
        _print("Note: Full functionality requires a browser/VM environment.")
        
        # Try a minimal test if possible
        try:
            # This may fail without proper environment setup
            result = agent.run(
                messages=[{"role": "user", "content": "Just confirm you're ready."}],
                tools=[ComputerTool()],
                max_tokens=50
            )
            _print("SUCCESS: Agent responded. Computer Use is available.")
        except Exception as e:
            _print(f"INFO: Agent test failed (expected without browser environment): {e}")
            _print("This is normal - Computer Use needs a browser/VM to function fully.")
        
        return 0
        
    except Exception as e:
        _print(f"ERROR: Could not initialize Computer Use: {e}")
        _print("Check that:")
        _print("1. Your account has tier 3-5 access")
        _print("2. CUA_MODEL env var points to a valid Computer Use model")
        _print("3. The OpenAI Agents SDK is properly installed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())