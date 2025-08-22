#!/usr/bin/env python3
"""Debug GPT-5 response extraction to see exactly what we're getting."""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def test_extraction():
    """Test extraction logic in detail."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    print("Calling GPT-5...")
    resp = client.responses.create(
        model="gpt-5",
        input=[
            {"role": "system", "content": "Return JSON: {\"test\": \"value\"}"},
            {"role": "user", "content": "Test"},
        ],
        max_output_tokens=100,
    )
    
    print(f"\nResponse type: {type(resp)}")
    print(f"Response.output type: {type(resp.output)}")
    print(f"Response.output length: {len(resp.output)}")
    
    for i, item in enumerate(resp.output):
        print(f"\nOutput[{i}]:")
        print(f"  Type: {type(item)}")
        print(f"  Item: {item}")
        
        if hasattr(item, 'type'):
            print(f"  Item.type: {item.type}")
        
        if hasattr(item, 'content'):
            print(f"  Item.content type: {type(item.content)}")
            if item.content:
                for j, content_item in enumerate(item.content):
                    print(f"    Content[{j}]:")
                    print(f"      Type: {type(content_item)}")
                    if hasattr(content_item, 'text'):
                        print(f"      Text: {repr(content_item.text)}")
                    if hasattr(content_item, 'type'):
                        print(f"      Type attr: {content_item.type}")
    
    # Now test the actual extraction logic
    print("\n" + "="*60)
    print("TESTING EXTRACTION LOGIC")
    print("="*60)
    
    c = None
    if hasattr(resp, 'output') and isinstance(resp.output, list):
        for item in resp.output:
            if hasattr(item, 'content') and item.content:
                for content_item in item.content:
                    if hasattr(content_item, 'text'):
                        c = content_item.text
                        print(f"✅ Extracted text: {repr(c)}")
                        break
            if c:
                break
    
    if c:
        print(f"\n✅ Final extracted content: {repr(c)}")
        try:
            parsed = json.loads(c)
            print(f"✅ Parsed JSON: {parsed}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            print(f"❌ Content was: {repr(c)}")
    else:
        print("❌ No content extracted")


if __name__ == "__main__":
    test_extraction()