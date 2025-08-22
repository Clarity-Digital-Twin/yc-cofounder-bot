"""Model resolution via OpenAI Models API.

Discovers available models at runtime instead of hardcoding.
Follows the fallback chain documented in AUDIT_AND_PLAN.md.
"""

from __future__ import annotations

import os
from typing import Any


def resolve_best_decision_model(client: Any) -> str:
    """Discover best GPT-5 model via Models API.

    Fallback chain:
    1. GPT-5 thinking variants (gpt-5-thinking, etc.)
    2. Any GPT-5 model
    3. GPT-4 variants (gpt-4o, gpt-4.1, etc.)
    4. Raise error if no suitable model

    Args:
        client: OpenAI client with models.list() method

    Returns:
        Best available model ID

    Raises:
        RuntimeError: If no suitable model found
    """
    try:
        models = client.models.list()
        ids = [m.id for m in models.data]
    except Exception as e:
        raise RuntimeError(f"Failed to list models: {e}") from e

    # 1. Try standard GPT-5 first (NOT gpt-5-thinking which doesn't exist!)
    if "gpt-5" in ids:
        print("✅ Found GPT-5 model!")
        return "gpt-5"
    
    # 2. Try GPT-5 variants (mini, nano)
    gpt5_variants = [m for m in ids if m.startswith("gpt-5-")]
    if gpt5_variants:
        selected = sorted(gpt5_variants)[0]  # Prefer gpt-5-mini over gpt-5-nano
        print(f"✅ Found GPT-5 variant: {selected}")
        return str(selected)

    # 3. Fallback to GPT-4 variants (despite user preference for GPT-5)
    gpt4_variants = [m for m in ids if m.lower().startswith("gpt-4")]
    if gpt4_variants:
        # Sort to get newest (gpt-4o, gpt-4.1, etc)
        selected = sorted(gpt4_variants, reverse=True)[0]
        print(f"⚠️ No GPT-5 available, using GPT-4 fallback: {selected}")
        return str(selected)

    # 4. Error if no suitable model
    raise RuntimeError(
        "No suitable GPT model found. Check API key and tier. "
        f"Available models: {', '.join(ids[:10]) if ids else 'none'}"
    )


def resolve_cua_model(client: Any) -> str | None:
    """Discover Computer Use model if available.

    Args:
        client: OpenAI client with models.list() method

    Returns:
        Computer Use model ID if available, None otherwise
    """
    try:
        models = client.models.list()
        ids = [m.id for m in models.data]
    except Exception as e:
        print(f"⚠️ Failed to list models for CUA: {e}")
        return None

    # Look for computer-use variants
    cua_models = [m for m in ids if "computer" in m.lower() or "cua" in m.lower()]
    if cua_models:
        selected = cua_models[0]
        print(f"✅ Found Computer Use model: {selected}")
        return str(selected)

    print("⚠️ No Computer Use model found (may need tier 3-5 access)")
    return None


def resolve_and_set_models(logger: Any | None = None) -> dict[str, str | None]:
    """Main entry point: Resolve models and set environment variables.

    This should be called once at application startup.
    Sets DECISION_MODEL_RESOLVED and CUA_MODEL_RESOLVED env vars.

    Args:
        logger: Optional logger for emitting events

    Returns:
        Dict with 'decision_model' and 'cua_model' keys
    """
    try:
        from openai import OpenAI
    except ImportError as e:
        raise RuntimeError("openai package not installed") from e

    # Create client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    client = OpenAI(api_key=api_key)

    # Resolve models
    decision_model = resolve_best_decision_model(client)
    cua_model = resolve_cua_model(client)

    # Set environment variables for downstream use
    os.environ["DECISION_MODEL_RESOLVED"] = decision_model
    if cua_model:
        os.environ["CUA_MODEL_RESOLVED"] = cua_model

    # Log what we're using
    result = {"decision_model": decision_model, "cua_model": cua_model}

    if logger:
        logger.emit(
            {
                "event": "models_resolved",
                "decision_model": decision_model,
                "cua_model": cua_model or "none",
                "fallback_used": "gpt-4" in decision_model.lower(),
            }
        )

    print("\n📊 Model Resolution Complete:")
    print(f"  Decision Model: {decision_model}")
    print(f"  CUA Model: {cua_model or 'Not available'}")

    return result
