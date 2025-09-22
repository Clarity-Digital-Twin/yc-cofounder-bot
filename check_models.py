#!/usr/bin/env python3
"""Check available OpenAI models"""

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

print("="*60)
print("CHECKING AVAILABLE OPENAI MODELS")
print("="*60)

models = client.models.list()
model_ids = sorted([m.id for m in models.data])

print(f"\nTotal models available: {len(model_ids)}")
print("\nGPT Models:")
for m in model_ids:
    if m.startswith('gpt'):
        print(f"  - {m}")

print("\nComputer Use Models:")
for m in model_ids:
    if 'computer' in m.lower() or 'cua' in m.lower():
        print(f"  - {m}")

print("\nO-Series Models:")
for m in model_ids:
    if m.startswith('o-') or m.startswith('o1') or m.startswith('o3'):
        print(f"  - {m}")

# Check specific models we care about
important_models = ['gpt-4o', 'gpt-4', 'gpt-5', 'computer-use-preview', 'gpt-4o-mini']
print("\nChecking specific models:")
for model in important_models:
    exists = model in model_ids
    print(f"  {model}: {'✅ Available' if exists else '❌ Not found'}")