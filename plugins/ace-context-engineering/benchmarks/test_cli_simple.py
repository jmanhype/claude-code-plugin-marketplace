#!/usr/bin/env python3
"""
Simple test to debug Claude CLI invocation issues
"""
import subprocess
import json
import time

def test_cli_with_curate_prompt():
    """Test CLI with a curate-delta style prompt"""

    prompt = """You are a curator.

Given this reflection output:
{
  "failure_type": "test failure",
  "key_insight": "Widget loading timeout",
  "specific_issues": ["timeout error", "async handling"]
}

Generate a minimal JSON delta proposal with this exact structure:
{
  "new_bullets": [],
  "counters": {}
}

Reply ONLY with valid JSON, no explanation."""

    print(f"Testing CLI with prompt ({len(prompt)} chars)...")
    print("="*80)

    start = time.time()

    # Use same command as the actual code
    cli_command = ['claude', '--print', '--output-format', 'json']

    print(f"Command: {' '.join(cli_command)}")
    print("Sending prompt via stdin...")

    result = subprocess.run(
        cli_command,
        input=prompt,
        text=True,
        capture_output=True,
        timeout=60
    )

    elapsed = time.time() - start

    print(f"\nCompleted in {elapsed:.2f}s")
    print(f"Exit code: {result.returncode}")
    print(f"Stdout length: {len(result.stdout)} chars")
    print(f"Stderr length: {len(result.stderr)} chars")

    if result.stderr:
        print(f"\nStderr:\n{result.stderr[:500]}")

    if result.stdout:
        try:
            response_json = json.loads(result.stdout)
            print(f"\n✅ Valid JSON response received")
            print(f"Keys: {list(response_json.keys())}")

            # Extract the actual result
            result_text = response_json.get('result', '')
            if result_text:
                print(f"\n📝 Result text ({len(result_text)} chars):")
                print(result_text[:500])

                # Try to parse the result as JSON
                try:
                    result_obj = json.loads(result_text)
                    print(f"\n✅ Result is valid JSON!")
                    print(f"Keys: {list(result_obj.keys())}")
                    print(json.dumps(result_obj, indent=2))
                except:
                    print(f"\n⚠️ Result is not JSON")
            else:
                print("\n❌ No result field in response!")
        except json.JSONDecodeError:
            print("\n❌ Response is not JSON!")
            print(result.stdout[:500])
    else:
        print("\n❌ Empty stdout!")

if __name__ == "__main__":
    test_cli_with_curate_prompt()