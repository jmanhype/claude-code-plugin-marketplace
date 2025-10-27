#!/usr/bin/env python3
"""
Test OAuth Flow for ACE
Run this to verify your OAuth credentials are working.
"""

import os
import sys
from pathlib import Path

# Add the utils directory to path
sys.path.insert(0, str(Path(__file__).parent / "benchmarks" / "utils"))

def test_oauth_flow():
    """Test the OAuth flow and get credentials."""

    print("=" * 80)
    print("ACE OAuth Flow Test")
    print("=" * 80)

    # Check required environment variables
    required_vars = [
        "ACE_OAUTH_AUTH_URL",
        "ACE_OAUTH_TOKEN_URL",
        "ACE_OAUTH_CLIENT_ID",
        "ACE_OAUTH_SCOPE",
        "ACE_OAUTH_BASE_URL",
        "NGROK_AUTHTOKEN"
    ]

    print("\n1. Checking environment variables...")
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✓ {var}: {'*' * 10} (set)")
        else:
            print(f"   ✗ {var}: NOT SET")
            missing.append(var)

    if missing:
        print("\n❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nPlease set these variables and try again.")
        print("\nExample setup:")
        print("export ACE_OAUTH_AUTH_URL='https://your-gateway.com/oauth/authorize'")
        print("export ACE_OAUTH_TOKEN_URL='https://your-gateway.com/oauth/token'")
        print("export ACE_OAUTH_CLIENT_ID='your-client-id'")
        print("export ACE_OAUTH_SCOPE='anthropic:messages:write'")
        print("export ACE_OAUTH_BASE_URL='https://your-gateway.com'")
        print("export NGROK_AUTHTOKEN='your-ngrok-token'")
        return False

    print("\n2. Testing ngrok availability...")
    import subprocess
    try:
        result = subprocess.run(["ngrok", "version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"   ✓ ngrok is installed: {result.stdout.strip()}")
        else:
            print("   ✗ ngrok command failed")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"   ✗ ngrok not found: {e}")
        print("\nPlease install ngrok:")
        print("   brew install ngrok  # macOS")
        print("   or download from https://ngrok.com/download")
        return False

    print("\n3. Attempting OAuth flow...")
    print("   This will:")
    print("   - Start ngrok tunnel")
    print("   - Open your browser for authorization")
    print("   - Wait for callback")
    print("   - Exchange code for token")

    try:
        from anthropic_oauth_client import build_oauth_client_from_env

        print("\n4. Initiating OAuth client...")
        client = build_oauth_client_from_env()

        print("\n5. Testing with a simple API call...")
        response = client.complete(
            "Say 'OAuth is working!' in exactly 5 words.",
            max_tokens=50
        )

        print("\n✅ Success! OAuth flow completed.")
        print(f"\nResponse from Claude: {response.text}")

        # Check if token was cached
        token_file = Path.home() / ".config" / "ace_oauth_token.json"
        if token_file.exists():
            print(f"\n✓ Token cached at: {token_file}")
            print("  (Future requests will use cached token)")

        return True

    except Exception as e:
        print(f"\n❌ OAuth flow failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your gateway is running")
        print("2. Verify client_id and client_secret are correct")
        print("3. Ensure ngrok authtoken is valid")
        print("4. Check firewall/network settings")
        return False

def test_skill_invocation():
    """Test skill invocation with OAuth."""
    print("\n" + "=" * 80)
    print("Testing Skill Invocation")
    print("=" * 80)

    try:
        from claude_code_skill_invoker import invoke_skill

        test_prompt = {
            "instruction": "Say hello",
            "apps": ["general"],
            "environment": {
                "mode": "test"
            }
        }

        import json
        response = invoke_skill(
            "generate-appworld-code",
            json.dumps(test_prompt)
        )

        print("\n✅ Skill invocation successful!")
        print(f"Response length: {len(response)} characters")
        print(f"First 200 chars: {response[:200]}...")
        return True

    except Exception as e:
        print(f"\n❌ Skill invocation failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting ACE OAuth Test...\n")

    # Test basic OAuth flow
    oauth_success = test_oauth_flow()

    if oauth_success:
        # If OAuth works, test skill invocation
        print("\nOAuth successful! Testing skill invocation...")
        test_skill_invocation()
    else:
        print("\n⚠️  Fix OAuth setup before testing skills")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)