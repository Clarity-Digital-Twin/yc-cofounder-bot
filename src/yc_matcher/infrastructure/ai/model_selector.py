"""Model selector - automatically choose best available model."""

import os
from typing import Optional

from openai import OpenAI


def get_best_available_model(client: Optional[OpenAI] = None) -> str:
    """Get the best available model from the user's OpenAI account.

    Priority order:
    1. GPT-5 models (if available)
    2. GPT-4o (multimodal, best GPT-4 class)
    3. GPT-4-turbo (faster GPT-4)
    4. GPT-4 (classic)

    Returns:
        Model ID string to use
    """
    # Check if explicitly set in environment
    explicit_model = os.getenv("OPENAI_DECISION_MODEL")
    if explicit_model:
        return explicit_model

    # Try to detect available models
    try:
        if not client:
            client = OpenAI()

        models = client.models.list()
        available_ids = [m.id for m in models.data]

        # Check for GPT-5 models (best)
        gpt5_models = [m for m in available_ids if "gpt-5" in m]
        if gpt5_models:
            # Prefer base gpt-5 over variants
            if "gpt-5" in gpt5_models:
                return "gpt-5"
            # Otherwise use first GPT-5 variant
            return sorted(gpt5_models)[0]

        # Check for GPT-4o (multimodal)
        if "gpt-4o" in available_ids:
            return "gpt-4o"

        # Check for GPT-4-turbo
        if "gpt-4-turbo" in available_ids:
            return "gpt-4-turbo"

        # Fallback to GPT-4
        if "gpt-4" in available_ids:
            return "gpt-4"

        # Ultimate fallback
        return "gpt-4o"  # Most likely to be available

    except Exception:
        # If can't list models, use safe default
        return os.getenv("OPENAI_DECISION_MODEL", "gpt-4o")


def is_gpt5_model(model_id: str) -> bool:
    """Check if a model ID is a GPT-5 variant."""
    return "gpt-5" in model_id.lower()


def should_use_responses_api(model_id: str) -> bool:
    """Determine if we should use Responses API for this model.

    GPT-5 models require Responses API.
    GPT-4 models use Chat Completions API.
    """
    return is_gpt5_model(model_id)