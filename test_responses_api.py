#!/usr/bin/env python3
"""Test if OpenAI Responses API exists in our SDK"""

from openai import OpenAI
import openai
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("="*60)
print("TESTING OPENAI RESPONSES API")
print("="*60)

# Check SDK version
print(f"SDK version: {openai.__version__}")

# Create client
client = OpenAI()

# Check if responses attribute exists
has_responses = hasattr(client, 'responses')
print(f"Has responses attribute: {has_responses}")

if has_responses:
    # Try a simple responses.create call
    try:
        print("\nTrying responses.create()...")
        response = client.responses.create(
            model='gpt-4o',
            input='Say hello'
        )
        print("✅ responses.create() WORKS!")
        print(f"Response type: {type(response)}")
        if hasattr(response, 'output_text'):
            print(f"Output: {response.output_text}")
    except Exception as e:
        print(f"❌ responses.create() failed: {e}")
else:
    print("\n❌ RESPONSES API NOT FOUND IN SDK")
    print("The client.responses attribute does not exist")

# Test chat.completions as fallback
print("\n" + "="*60)
print("TESTING CHAT COMPLETIONS (FALLBACK)")
print("="*60)

try:
    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=50
    )
    print("✅ chat.completions.create() WORKS!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ chat.completions failed: {e}")