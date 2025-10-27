#!/usr/bin/env python3
"""
Test the PTY-based curator implementation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils.claude_code_skill_invoker import invoke_skill

def test_curator_with_pty():
    """Test curate-delta skill with new PTY implementation"""

    print("="*80)
    print("Testing PTY-based curator implementation")
    print("="*80)

    # Create a simple curation request
    prompt = """
Given this reflection output:

{
  "failure_type": "test failure",
  "key_insight": "Widget loading timeout - needs async handling",
  "specific_issues": [
    "timeout error on widget.load()",
    "missing await statement"
  ],
  "suggested_bullet": {
    "title": "Add async/await for widget operations",
    "content": "Widget loading operations need proper async/await patterns to prevent timeout errors",
    "tags": ["async", "widgets", "timeout"]
  }
}

Generate a delta proposal that includes:
1. The suggested bullet as a new bullet
2. Increment the counter for "async_patterns_needed"

Output only valid JSON.
"""

    try:
        # Invoke curator skill
        print("\n📤 Sending curation request...")
        print(f"Prompt length: {len(prompt)} chars")

        response = invoke_skill("curate-delta", prompt)

        print(f"\n✅ Got response ({len(response)} chars)")
        print("\n📝 Response:")
        print("-"*40)
        print(response)
        print("-"*40)

        # Try to parse as JSON
        import json
        try:
            result = json.loads(response)
            print("\n✅ Valid JSON response!")
            print(f"Keys: {list(result.keys())}")
            if "delta" in result:
                delta = result["delta"]
                print(f"Delta keys: {list(delta.keys())}")
                print(f"New bullets: {len(delta.get('new_bullets', []))}")
                print(f"Counters: {len(delta.get('counters', {}))}")

                if delta.get('new_bullets'):
                    print("\nNew bullets:")
                    for bullet in delta['new_bullets']:
                        print(f"  - {bullet.get('title', 'No title')}")

                if delta.get('counters'):
                    print("\nCounters:")
                    for key, value in delta['counters'].items():
                        print(f"  - {key}: {value}")
        except json.JSONDecodeError:
            print("\n⚠️ Response is not valid JSON")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_curator_with_pty()