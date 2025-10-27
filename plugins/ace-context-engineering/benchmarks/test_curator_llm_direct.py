#!/usr/bin/env python3
"""
Test the Curator's LLM invocation directly to see what's being returned.
"""

import sys
import json
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / 'utils'))

import claude_code_skill_invoker as skill_invoker


def test_curator_llm():
    """Test what the curate-delta skill actually returns."""

    # Build a simple test prompt
    test_prompt = """# Task Metadata
Instruction: Find the most-liked song in Spotify playlists
Outcome: Failure (TGC: 0.5, SGC: 0.5)

## Execution Summary
- Turns used: 3
- Error type: logic_error
- Error messages: Tests failed: 1/2
- Missing patterns: Check task logic
- Failed APIs: general.login

## Reflector's Proposed Delta
```json
{
  "new_bullets": [
    {
      "id": "bullet-test-001",
      "title": "Always login before API calls",
      "content": "Call login() for the app before using any API methods",
      "tags": ["api", "authentication"]
    }
  ],
  "counters": {},
  "error_type": "logic_error"
}
```

## Your Task
Synthesize the Reflector's output into a high-quality delta proposal.
- Validate bullet quality (specific, actionable, evidence-backed)
- Check for redundancy with existing bullets
- Structure counter updates for bullet feedback
- Provide curation notes and quality assessment

Return your response as valid JSON with this structure:
{
  "delta": {
    "new_bullets": [...],
    "counters": [...]
  },
  "curation_notes": [...],
  "quality_score": 0.0-1.0
}"""

    print("=" * 80)
    print("Testing curate-delta skill direct invocation")
    print("=" * 80)
    print(f"Prompt length: {len(test_prompt)} chars")
    print()

    try:
        # Invoke the skill
        response = skill_invoker.invoke_skill("curate-delta", test_prompt)

        print(f"\n✅ Got response ({len(response)} chars)")
        print("\n📝 RAW RESPONSE:")
        print("-" * 40)
        print(response)
        print("-" * 40)

        # Try to parse as JSON
        print("\n🔍 Attempting JSON parse...")
        try:
            # Clean response if wrapped in code fence
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
                if response_clean.endswith('```'):
                    response_clean = response_clean[:-3]
                response_clean = response_clean.strip()
            elif response_clean.startswith('```'):
                response_clean = response_clean[3:]
                if response_clean.endswith('```'):
                    response_clean = response_clean[:-3]
                response_clean = response_clean.strip()

            # Try parsing
            parsed = json.loads(response_clean)
            print("✅ Successfully parsed as JSON!")
            print(f"Keys: {list(parsed.keys())}")

            if 'delta' in parsed:
                print(f"Delta keys: {list(parsed['delta'].keys())}")
                print(f"New bullets: {len(parsed['delta'].get('new_bullets', []))}")
                print(f"Counters: {len(parsed['delta'].get('counters', []))}")

        except json.JSONDecodeError as e:
            print(f"❌ JSON parse failed: {e}")
            print(f"First 100 chars of cleaned response: {response_clean[:100]}")

            # Try to find JSON in response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                print("\n🔍 Found JSON-like content in response:")
                print(json_match.group()[:200] + "...")

    except Exception as e:
        print(f"\n❌ Skill invocation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_curator_llm()