from __future__ import annotations

import os
import sys
from typing import Any, Optional

try:
    from dotenv import load_dotenv as _load_dotenv
except Exception:  # pragma: no cover
    _load_dotenv = None  # type: ignore[assignment]


def _print(msg: str) -> None:
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def main() -> int:
    if _load_dotenv is not None:
        _load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        _print("ERROR: OPENAI_API_KEY not set. Add it to .env or your environment.")
        return 2

    try:
        from openai import OpenAI
    except Exception as e:  # pragma: no cover
        _print(f"ERROR: openai package not installed or incompatible: {e}")
        return 2

    client: Any = OpenAI(api_key=api_key)

    # Step 1: model availability
    try:
        models = client.models.list()
        model_ids = {m.id for m in models.data}
        has_alias = any(mid.startswith("computer-use-preview") for mid in model_ids) or (
            "computer-use-preview" in model_ids
        )
        _print(
            "Models visible: "
            + ("has computer-use-preview" if has_alias else "computer-use-preview not listed")
        )
    except Exception as e:
        _print(f"Warning: could not list models: {e}")

    # Step 2: minimal Responses call with computer-use tool
    tool_variants: list[dict[str, Any]] = [
        {"type": "computer_use", "display_width": 1024, "display_height": 768, "environment": "browser"},
        {"type": "computer_use_preview", "display_width": 1024, "display_height": 768, "environment": "browser"},
    ]
    last_err: Exception | None = None
    for tool in tool_variants:
        try:
            responses = getattr(client, "responses", None)
            if responses is None:
                raise AttributeError("responses not available on OpenAI client")
            responses.create(
                model="computer-use-preview",
                input="Just confirm you can see a browser environment.",
                tools=[tool],
                max_output_tokens=64,
            )
            _print(f"SUCCESS: Access ok with tool type '{tool['type']}'.")
            _print("Note: This was a dry probe; full agent loop comes later.")
            return 0
        except Exception as e:
            last_err = e
            continue

    _print("ERROR: Could not use computer-use-preview. Last error:\n" + str(last_err))
    _print("Check that your account has access to the Computer Use preview model.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
