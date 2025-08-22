#!/usr/bin/env python
"""Check what OpenAI models are actually available."""

import os
from openai import OpenAI

# Load API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ OPENAI_API_KEY not set")
    exit(1)

client = OpenAI(api_key=api_key)

print("\n📊 Available OpenAI Models:\n")
print("-" * 60)

try:
    models = client.models.list()
    model_ids = sorted([m.id for m in models.data])
    
    # Group by prefix
    gpt5_models = [m for m in model_ids if m.startswith("gpt-5")]
    gpt4_models = [m for m in model_ids if m.startswith("gpt-4")]
    o_models = [m for m in model_ids if m.startswith("o1") or m.startswith("o3")]
    other_models = [m for m in model_ids if not (m.startswith("gpt-") or m.startswith("o1") or m.startswith("o3"))]
    
    if gpt5_models:
        print("✅ GPT-5 Models:")
        for m in gpt5_models:
            print(f"   - {m}")
    else:
        print("❌ No GPT-5 models found")
    
    print()
    
    if gpt4_models:
        print("✅ GPT-4 Models:")
        for m in gpt4_models[:5]:  # Show first 5
            print(f"   - {m}")
        if len(gpt4_models) > 5:
            print(f"   ... and {len(gpt4_models)-5} more")
    
    print()
    
    if o_models:
        print("✅ O-series Models:")
        for m in o_models:
            print(f"   - {m}")
    
    print("\n" + "-" * 60)
    print(f"Total models available: {len(model_ids)}")
    
    # Check what's in env
    print("\n📝 Environment Settings:")
    print(f"   OPENAI_DECISION_MODEL = {os.getenv('OPENAI_DECISION_MODEL')}")
    print(f"   DECISION_MODEL_RESOLVED = {os.getenv('DECISION_MODEL_RESOLVED')}")
    
except Exception as e:
    print(f"❌ Error listing models: {e}")