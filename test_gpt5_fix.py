#!/usr/bin/env python3
"""Test GPT-5 Responses API with fixed parameters."""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def test_gpt5_responses():
    """Test that GPT-5 Responses API works with fixed parameters."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    sys_prompt = (
        "You are an expert recruiter evaluating potential co-founder matches. "
        "You MUST return a valid JSON object with these exact keys:\n"
        "- decision: string 'YES' or 'NO'\n"
        "- rationale: string explaining your reasoning in 1-2 sentences\n"
        "- score: float between 0.0 and 1.0 indicating match strength\n"
        "Your entire response must be valid JSON - no other text before or after the JSON object."
    )
    
    user_text = (
        "MY CRITERIA: Looking for a technical co-founder with Python experience.\n\n"
        "CANDIDATE PROFILE: I'm a full-stack engineer with 10 years of Python experience.\n\n"
        "Evaluate if this candidate matches my criteria.\n"
        "IMPORTANT: Return your response as valid JSON."
    )
    
    try:
        print("Testing GPT-5 Responses API with fixed parameters...")
        resp = client.responses.create(
            model="gpt-5",
            input=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_text},
            ],
            max_output_tokens=800,  # Fixed: using max_output_tokens
        )
        
        # Extract content from Responses API format
        content = resp.output_text if hasattr(resp, 'output_text') else str(resp.output[0])
        
        print(f"✅ Response received: {content[:100]}...")
        
        # Try to parse as JSON
        result = json.loads(content)
        print(f"✅ Valid JSON parsed!")
        print(f"Decision: {result.get('decision')}")
        print(f"Rationale: {result.get('rationale')}")
        print(f"Score: {result.get('score')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_gpt5_responses()
    exit(0 if success else 1)