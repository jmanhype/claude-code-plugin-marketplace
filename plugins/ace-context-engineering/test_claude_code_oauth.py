#!/usr/bin/env python3
"""
Test Claude Code with OAuth credentials
"""

import os
from pathlib import Path

# Load environment
env_file = Path.home() / ".config" / "ace_claude_max.env"
if env_file.exists():
    print(f"Loading configuration from: {env_file}")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and line.startswith('export '):
                # Parse: export KEY="value"
                parts = line[7:].split('=', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().strip('"').strip("'")
                    os.environ[key] = value
                    print(f"  ✓ {key}")

print()
print("=" * 80)
print("Testing Claude Code with OAuth Credentials")
print("=" * 80)
print()

# Test using Anthropic SDK directly
try:
    import anthropic

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        exit(1)

    print(f"API Key: {api_key[:30]}...")
    print()

    client = anthropic.Anthropic(api_key=api_key)

    print("Sending test request to Claude API...")
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[
            {"role": "user", "content": "Say 'Claude Code OAuth test successful!' and nothing else."}
        ]
    )

    response_text = message.content[0].text
    print(f"✅ Response: {response_text}")
    print()
    print("🎉 Claude Code OAuth setup is working!")

except ImportError:
    print("⚠️  anthropic package not installed. Installing...")
    import subprocess
    subprocess.run(["pip", "install", "anthropic"], check=True)
    print()
    print("Anthropic installed! Please run this script again.")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
