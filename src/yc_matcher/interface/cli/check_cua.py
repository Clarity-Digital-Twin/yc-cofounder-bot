"""Check OpenAI Computer Use access via Responses API.

This CLI verifies that:
- `OPENAI_API_KEY` is set and the OpenAI SDK is usable
- The configured `CUA_MODEL` is accessible
- A minimal Responses API call with the `computer_use_preview` tool works

It does NOT require the legacy Agents SDK and does not attempt to launch a
browser; it only checks that your account can call the CUA tool via the
Responses API.
"""

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

    # Step 2: Try a minimal Responses API call with computer_use_preview
    try:
        cua_model = os.getenv("CUA_MODEL")
        if not cua_model:
            _print("WARNING: CUA_MODEL not set. Check your Models endpoint.")
            _print("Visit: https://platform.openai.com/account/models")
            return 1

        # Minimal probe: do not require a browser. Ask the model to just reply "ready".
        # This validates that the account can call the model with the CUA tool.
        resp = client.responses.create(
            model=cua_model,
            tools=[
                {
                    "type": "computer_use_preview",
                    "display_width": 1280,
                    "display_height": 800,
                    "environment": "browser",
                }
            ],
            input=[
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": "Just reply: ready."}],
                }
            ],
            truncation="auto",
            max_output_tokens=50,
        )

        # Success if call returns; extract any text if available for display
        output_text = getattr(resp, "output_text", None)
        if not output_text:
            # Fallback to manual extraction for older SDK variants
            try:
                parts = []
                for item in getattr(resp, "output", []) or []:
                    if getattr(item, "type", "") == "message" and hasattr(item, "content"):
                        if isinstance(item.content, list):
                            for c in item.content:
                                if hasattr(c, "text"):
                                    parts.append(c.text)
                        elif isinstance(item.content, str):
                            parts.append(item.content)
                output_text = "".join(parts) if parts else None
            except Exception:
                output_text = None

        _print(f"SUCCESS: Responses API call succeeded for model: {cua_model}")
        if output_text:
            preview = output_text.strip().splitlines()[0][:120]
            _print(f"Preview: {preview}")
        else:
            _print("Note: No textual output returned (ok for CUA probes).")
        return 0

    except Exception as e:
        _print(f"ERROR: Responses API call failed: {e}")
        _print("Check that:")
        _print("1. Your account has tier 3-5 access")
        _print("2. CUA_MODEL env var points to a valid Computer Use model")
        _print("3. The Responses API is available in your SDK version")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
