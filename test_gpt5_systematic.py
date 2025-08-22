#!/usr/bin/env python3
"""Systematic testing of GPT-5 Responses API to understand exact behavior."""

import os
import json
import sys
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def test_raw_response():
    """Test 1: Get raw response from GPT-5 to see what it actually returns."""
    print("\n" + "="*60)
    print("TEST 1: RAW GPT-5 RESPONSE")
    print("="*60)
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    try:
        print("Calling GPT-5 with simple prompt...")
        resp = client.responses.create(
            model="gpt-5",
            input=[{"role": "user", "content": "Say 'hello world'"}],
            max_output_tokens=10,
        )
        
        print(f"\n✅ Response object type: {type(resp)}")
        print(f"✅ Response attributes: {dir(resp)}")
        
        # Try different ways to extract content
        if hasattr(resp, 'output_text'):
            print(f"✅ output_text: {repr(resp.output_text)}")
        if hasattr(resp, 'output'):
            print(f"✅ output: {repr(resp.output)}")
            if resp.output and len(resp.output) > 0:
                print(f"✅ output[0]: {repr(resp.output[0])}")
                if hasattr(resp.output[0], 'content'):
                    print(f"✅ output[0].content: {repr(resp.output[0].content)}")
        if hasattr(resp, 'choices'):
            print(f"✅ choices: {repr(resp.choices)}")
            
        return resp
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        return None


def test_json_request():
    """Test 2: Request JSON format explicitly in prompt."""
    print("\n" + "="*60)
    print("TEST 2: JSON REQUEST IN PROMPT")
    print("="*60)
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompt = '''Return ONLY valid JSON with these keys:
{"decision": "YES", "score": 0.8}
No other text, just JSON.'''
    
    try:
        print("Requesting JSON output...")
        resp = client.responses.create(
            model="gpt-5",
            input=[{"role": "user", "content": prompt}],
            max_output_tokens=50,
        )
        
        # Extract content
        if hasattr(resp, 'output_text'):
            content = resp.output_text
        elif hasattr(resp, 'output') and resp.output:
            content = str(resp.output[0])
        else:
            content = str(resp)
            
        print(f"\n✅ Raw content: {repr(content)}")
        
        # Try to parse as JSON
        try:
            parsed = json.loads(content)
            print(f"✅ Parsed JSON: {parsed}")
            return parsed
        except json.JSONDecodeError as je:
            print(f"❌ JSON parse failed: {je}")
            print(f"❌ Content was: {repr(content[:100])}")
            return None
            
    except Exception as e:
        print(f"❌ API Error: {e}")
        return None


def test_with_system_prompt():
    """Test 3: Use system prompt for JSON instruction."""
    print("\n" + "="*60)
    print("TEST 3: SYSTEM PROMPT FOR JSON")
    print("="*60)
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    try:
        print("Using system prompt for JSON...")
        resp = client.responses.create(
            model="gpt-5",
            input=[
                {"role": "system", "content": "You are a JSON-only assistant. Return only valid JSON objects."},
                {"role": "user", "content": "Evaluate this: test. Return {decision, score}"},
            ],
            max_output_tokens=100,
        )
        
        # Extract content
        if hasattr(resp, 'output_text'):
            content = resp.output_text
        elif hasattr(resp, 'output') and resp.output:
            if hasattr(resp.output[0], 'content'):
                content = resp.output[0].content
            else:
                content = str(resp.output[0])
        else:
            content = str(resp)
            
        print(f"\n✅ Raw content: {repr(content)}")
        
        # Try to parse
        try:
            parsed = json.loads(content)
            print(f"✅ Parsed JSON: {parsed}")
            return parsed
        except json.JSONDecodeError as je:
            print(f"❌ JSON parse failed: {je}")
            # Try to extract JSON from text
            import re
            json_match = re.search(r'\{[^}]*\}', content)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    print(f"✅ Extracted JSON: {parsed}")
                    return parsed
                except:
                    pass
            return None
            
    except Exception as e:
        print(f"❌ API Error: {e}")
        return None


def test_actual_evaluation():
    """Test 4: Actual evaluation like the app does."""
    print("\n" + "="*60)
    print("TEST 4: ACTUAL EVALUATION PROMPT")
    print("="*60)
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    sys_prompt = (
        "You are an expert recruiter evaluating potential co-founder matches. "
        "You MUST return a valid JSON object with these exact keys:\n"
        "- decision: string 'YES' or 'NO'\n"
        "- rationale: string explaining your reasoning in 1-2 sentences\n"
        "- draft: if YES, a personalized message to the candidate (if NO, empty string)\n"
        "- score: float between 0.0 and 1.0 indicating match strength\n"
        "- confidence: float between 0.0 and 1.0 indicating your confidence\n\n"
        "Your entire response must be valid JSON - no other text before or after the JSON object."
    )
    
    user_text = (
        "MY CRITERIA: Looking for Python developer.\n\n"
        "CANDIDATE PROFILE: I have 10 years Python experience.\n\n"
        "IMPORTANT: Return your response as valid JSON."
    )
    
    try:
        print("Testing actual evaluation prompt...")
        resp = client.responses.create(
            model="gpt-5",
            input=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_text},
            ],
            max_output_tokens=800,
        )
        
        # Debug: print full response object
        print(f"\n✅ Response type: {type(resp)}")
        print(f"✅ Response: {resp}")
        
        # Try all extraction methods
        content = None
        if hasattr(resp, 'output_text'):
            content = resp.output_text
            print(f"✅ Found output_text: {repr(content[:100])}")
        elif hasattr(resp, 'output') and resp.output:
            if isinstance(resp.output, list) and len(resp.output) > 0:
                first_output = resp.output[0]
                print(f"✅ First output type: {type(first_output)}")
                if hasattr(first_output, 'content'):
                    content = first_output.content
                elif hasattr(first_output, 'text'):
                    content = first_output.text
                else:
                    content = str(first_output)
                print(f"✅ Extracted from output[0]: {repr(content[:100])}")
        
        if not content:
            print("❌ No content extracted from response")
            return None
            
        # Try to parse
        try:
            parsed = json.loads(content)
            print(f"✅ Successfully parsed JSON: {parsed}")
            return parsed
        except json.JSONDecodeError as je:
            print(f"❌ JSON parse failed: {je}")
            print(f"❌ Full content: {repr(content)}")
            return None
            
    except Exception as e:
        print(f"❌ API Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all tests systematically."""
    print("\n" + "="*80)
    print("SYSTEMATIC GPT-5 TESTING")
    print("="*80)
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ No OPENAI_API_KEY found")
        return 1
        
    print(f"✅ API Key: ...{os.getenv('OPENAI_API_KEY')[-8:]}")
    
    # Run tests
    tests = [
        ("Raw Response", test_raw_response),
        ("JSON Request", test_json_request),
        ("System Prompt", test_with_system_prompt),
        ("Actual Evaluation", test_actual_evaluation),
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
        
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name}: {status}")
        
    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    if all(r[1] for r in results):
        print("✅ All tests passed - GPT-5 is working correctly")
    else:
        print("❌ Some tests failed - issues found:")
        print("1. Check if GPT-5 returns output in expected format")
        print("2. May need to adjust content extraction logic")
        print("3. Consider fallback to GPT-4 if GPT-5 unavailable")
        
    return 0 if all(r[1] for r in results) else 1


if __name__ == "__main__":
    exit(main())