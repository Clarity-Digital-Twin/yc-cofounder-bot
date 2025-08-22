#!/usr/bin/env python
"""Check what OpenAI models are available."""

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

client = OpenAI()

print("Available models in your account:")
print("-" * 50)

models = client.models.list()
gpt_models = []

for model in models:
    if 'gpt' in model.id.lower():
        gpt_models.append(model.id)

# Sort and display
gpt_models.sort(reverse=True)  # Newest first

print("\nGPT Models available:")
for m in gpt_models[:20]:  # Show top 20
    if '5' in m:
        print(f"  ⭐ {m} (GPT-5 model!)")
    else:
        print(f"  • {m}")

print("\nLooking for GPT-5 models specifically...")
gpt5_models = [m for m in gpt_models if '5' in m or 'five' in m.lower()]
if gpt5_models:
    print(f"Found GPT-5 models: {gpt5_models}")
else:
    print("No GPT-5 models found. Using GPT-4o is the best available.")