#!/usr/bin/env python
"""Test GPT-5 access with correct model ID."""

import os
from openai import OpenAI

# Load API key
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

print("\n🔍 Testing GPT-5 Access...\n")

# First check if model exists
models = client.models.list()
model_ids = [m.id for m in models.data]

if "gpt-5" in model_ids:
    print("✅ GPT-5 is available on your account!")
else:
    print("❌ GPT-5 not found. Available GPT models:")
    gpt_models = [m for m in model_ids if m.startswith("gpt-")]
    for m in sorted(gpt_models)[:10]:
        print(f"   - {m}")

# Try a simple call with Chat Completions API (current method)
try:
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": "Say 'GPT-5 works!'"}],
        max_tokens=10
    )
    print(f"\n✅ GPT-5 Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"\n❌ Chat Completions API Error: {e}")

print("\n" + "="*60)
print("IMPORTANT: GPT-5 uses the Responses API, not Chat Completions!")
print("Your code needs to be updated to use client.responses.create()")
print("="*60)