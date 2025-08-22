#!/usr/bin/env python
"""Test GPT-4.1 model."""

from dotenv import load_dotenv
load_dotenv()

import os
from openai import OpenAI

client = OpenAI()
model = os.getenv("OPENAI_DECISION_MODEL")

print(f"Testing model: {model}")

try:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello from GPT-4.1!' if you're working."}
        ],
        max_tokens=50
    )
    
    print(f"✅ Success! Response: {response.choices[0].message.content}")
    print(f"Model used: {response.model}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Falling back to gpt-4o...")
    
    # Try with gpt-4o as fallback
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello from GPT-4o!' if you're working."}
        ],
        max_tokens=50
    )
    print(f"✅ Fallback worked: {response.choices[0].message.content}")