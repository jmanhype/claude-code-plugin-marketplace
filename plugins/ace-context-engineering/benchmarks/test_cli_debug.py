#!/usr/bin/env python3
"""
Deep debug test for Claude CLI invocation issues
"""
import subprocess
import json
import sys
import time
from pathlib import Path

def test_cli_invocation(prompt, method_name="test"):
    """Test different CLI invocation methods"""
    print(f"\n{'='*80}")
    print(f"Method: {method_name}")
    print(f"Prompt length: {len(prompt)} chars")
    print(f"{'='*80}")

    start_time = time.time()

    # Method 1: Direct with --output-format json
    if method_name == "json_format":
        cmd = ['claude', '--print', '--output-format', 'json']
    # Method 2: With explicit model
    elif method_name == "with_model":
        cmd = ['claude', '--print', '--model', 'claude-3-5-sonnet-20241022', '--output-format', 'json']
    # Method 3: Using chat mode
    elif method_name == "chat_mode":
        cmd = ['claude', 'chat', '--print', '--output-format', 'json']
    # Method 4: With max-tokens
    elif method_name == "with_max_tokens":
        cmd = ['claude', '--print', '--output-format', 'json', '--max-tokens', '4000']
    else:
        cmd = ['claude', '--print', '--output-format', 'json']

    print(f"Command: {' '.join(cmd)}")
    print(f"Sending prompt via stdin...")

    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=120
        )

        elapsed = time.time() - start_time
        print(f"Elapsed time: {elapsed:.2f}s")
        print(f"Exit code: {result.returncode}")

        # Capture raw outputs
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        print(f"\n--- STDOUT (length: {len(stdout)} chars) ---")
        if stdout:
            # Try to parse as JSON for pretty printing
            try:
                parsed = json.loads(stdout)
                print("✅ Valid JSON response:")
                print(json.dumps(parsed, indent=2)[:1000])  # First 1000 chars

                # Extract the actual result
                result_text = (
                    parsed.get('result') or
                    parsed.get('text') or
                    parsed.get('completion') or
                    ''
                )

                if result_text:
                    print(f"\n✅ Extracted result text ({len(result_text)} chars):")
                    print(result_text[:500])
                else:
                    print("\n⚠️ JSON response has no text content!")
                    print(f"Available keys: {list(parsed.keys())}")

            except json.JSONDecodeError as e:
                print(f"⚠️ Not JSON: {e}")
                print(stdout[:500])
        else:
            print("❌ EMPTY STDOUT!")

        print(f"\n--- STDERR (length: {len(stderr)} chars) ---")
        if stderr:
            print(stderr[:500])
        else:
            print("(empty)")

        return stdout, stderr, result.returncode

    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT after 120s")
        return "", "", -1
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return "", "", -1

def main():
    # Test with simple prompts first
    simple_prompt = "Reply with a JSON object containing one field 'status' with value 'ok'"

    print("\n" + "="*80)
    print("SIMPLE PROMPT TEST")
    print("="*80)

    for method in ["json_format", "with_model", "with_max_tokens"]:
        test_cli_invocation(simple_prompt, method)
        time.sleep(2)  # Avoid rate limiting

    # Now test with a complex ACE prompt
    complex_prompt = """You are a curator analyzing reflection insights.

Given this reflection:
{
  "failure_type": "test failure",
  "key_insight": "Widget loading timeout",
  "specific_issues": ["timeout error", "async handling"]
}

Generate a minimal JSON delta proposal:
{
  "new_bullets": [],
  "counters": {}
}

Reply ONLY with valid JSON, no explanation."""

    print("\n" + "="*80)
    print("COMPLEX ACE PROMPT TEST")
    print("="*80)

    for method in ["json_format", "with_model", "with_max_tokens"]:
        test_cli_invocation(complex_prompt, method)
        time.sleep(2)

if __name__ == "__main__":
    main()