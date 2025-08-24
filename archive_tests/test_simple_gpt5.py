#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Load .env
env_file = Path('.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                if '#' in value:
                    value = value.split('#')[0].strip()
                os.environ[key] = value

sys.path.insert(0, 'src')

from openai import OpenAI  # noqa: E402

client = OpenAI()
model = os.getenv("OPENAI_DECISION_MODEL", "gpt-5")

print(f"Testing {model} with simple JSON request...")

# Simple test
response = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": "You are a helpful assistant. Always respond with valid JSON."},
        {"role": "user", "content": 'Evaluate this match and respond with JSON: {"decision": "YES" or "NO", "reason": "short reason"}. Profile: Technical founder in SF looking for business cofounder. Candidate: Dr. Juan in Rhode Island, willing to do sales.'}
    ],
    response_format={"type": "json_object"},
    temperature=1  # GPT-5 requires temperature=1
)

print("Response:", response.choices[0].message.content)
