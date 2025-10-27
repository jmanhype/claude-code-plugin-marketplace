#!/usr/bin/env python3
"""
Debug version of OAuth Flow test for Claude Max Subscription
Shows detailed information about the OAuth process.
"""

import os
import sys
import subprocess
import time
import traceback
from pathlib import Path

# Add the utils directory to path
sys.path.insert(0, str(Path(__file__).parent / "benchmarks" / "utils"))

def check_ngrok():
    """Check if ngrok is available and configured."""
    try:
        # Check if ngrok is installed
        result = subprocess.run(["ngrok", "version"], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return False, "ngrok command failed"

        # Check for authtoken
        ngrok_token = os.getenv("NGROK_AUTHTOKEN")
        if not ngrok_token:
            # Try to read from ngrok config
            config_path = Path.home() / ".ngrok2" / "ngrok.yml"
            if config_path.exists():
                return True, "ngrok configured (config file found)"
            else:
                return False, "ngrok authtoken not configured"

        return True, f"ngrok ready (token: {ngrok_token[:10]}...)"

    except FileNotFoundError:
        return False, "ngrok not installed"
    except Exception as e:
        return False, str(e)

def test_claude_max_oauth_debug():
    """Test OAuth flow with Claude Max subscription with debugging."""

    print("=" * 80)
    print("Claude Max OAuth Flow Test (DEBUG MODE)")
    print("=" * 80)
    print()

    # Step 1: Check environment
    print("1. Checking configuration...")

    required_set = True

    # Check Claude OAuth endpoints
    auth_url = os.getenv("ACE_OAUTH_AUTH_URL")
    if auth_url == "https://console.anthropic.com/oauth/authorize":
        print("   ✓ Auth URL: Claude.ai OAuth endpoint")
    else:
        print(f"   ✗ Auth URL not set correctly: {auth_url}")
        required_set = False

    token_url = os.getenv("ACE_OAUTH_TOKEN_URL")
    if token_url == "https://api.anthropic.com/oauth/token":
        print("   ✓ Token URL: Claude API endpoint")
    else:
        print(f"   ✗ Token URL not set correctly: {token_url}")
        required_set = False

    client_id = os.getenv("ACE_OAUTH_CLIENT_ID")
    if client_id == "9d1c250a-e61b-44d9-88ed-5944d1962f5e":
        print("   ✓ Client ID: Official Claude Code ID")
    else:
        print(f"   ✗ Client ID not set correctly: {client_id}")
        required_set = False

    # Show scope
    scope = os.getenv("ACE_OAUTH_SCOPE")
    print(f"   ℹ Scope: {scope}")

    # Show base URL
    base_url = os.getenv("ACE_OAUTH_BASE_URL")
    print(f"   ℹ Base URL: {base_url}")

    # Check ngrok
    print()
    print("2. Checking ngrok...")
    ngrok_ready, ngrok_msg = check_ngrok()
    if ngrok_ready:
        print(f"   ✓ {ngrok_msg}")
    else:
        print(f"   ✗ {ngrok_msg}")
        print()
        print("   To set up ngrok:")
        print("   1. Sign up at https://ngrok.com (free)")
        print("   2. Get your authtoken from the dashboard")
        print("   3. Run: ngrok config add-authtoken YOUR_TOKEN")
        print("      Or set: export NGROK_AUTHTOKEN='your-token'")
        required_set = False

    if not required_set:
        print()
        print("❌ Configuration incomplete. Please:")
        print("   1. Run: source claude_max_oauth.env")
        print("   2. Set up ngrok if needed")
        return False

    # Step 2: Test the OAuth flow
    print()
    print("3. Starting OAuth flow...")
    print("   This will:")
    print("   • Start ngrok tunnel for OAuth callback")
    print("   • Open your browser to Claude login")
    print("   • Capture the OAuth token after you authorize")
    print()

    try:
        from anthropic_oauth_client import build_oauth_client_from_env

        print("Starting OAuth authentication...")
        print("(Your browser will open in a moment)")
        print()

        print("DEBUG: Importing OAuth client...")
        print(f"DEBUG: Environment variables:")
        for key in ["ACE_OAUTH_AUTH_URL", "ACE_OAUTH_TOKEN_URL", "ACE_OAUTH_CLIENT_ID", "ACE_OAUTH_SCOPE", "ACE_OAUTH_BASE_URL"]:
            print(f"       {key}: {os.getenv(key)}")
        print()

        # This will trigger the full OAuth flow
        print("DEBUG: Building OAuth client...")
        client = build_oauth_client_from_env()

        print("✅ OAuth authentication successful!")
        print()

        # Test with a simple request
        print("4. Testing Claude Max access...")
        print("DEBUG: Sending test message...")

        try:
            response = client.complete(
                "Say 'Claude Max is working!' in exactly 4 words.",
                max_tokens=50
            )
            print(f"   Response: {response.text}")
            print()
        except Exception as api_error:
            print(f"   ❌ API call failed: {api_error}")
            print(f"   DEBUG: Full error:\n{traceback.format_exc()}")

        # Check token cache
        token_file = Path(os.getenv("ACE_OAUTH_TOKEN_FILE", "~/.config/ace_claude_max_token.json")).expanduser()
        if token_file.exists():
            print("✓ Token cached successfully at:")
            print(f"  {token_file}")
            print()
            print("  Future requests will use this cached token.")
            print("  Token will auto-refresh when needed.")
            print("  No browser login required until token expires!")

        return True

    except Exception as e:
        print(f"❌ OAuth flow failed: {e}")
        print()

        print(f"DEBUG: Full traceback:")
        print(traceback.format_exc())
        print()

        if "Missing required OAuth environment variables" in str(e):
            print("Please run: source claude_max_oauth.env")
        elif "Failed to obtain ngrok public URL" in str(e):
            print("ngrok couldn't start. Check your authtoken.")
        elif "OAuth2 state mismatch" in str(e):
            print("The OAuth callback failed. Try again.")
        elif "Token endpoint error" in str(e):
            print("Token exchange failed. This might be a scope or configuration issue.")
        else:
            print("Troubleshooting:")
            print("1. Make sure you have a Claude Max subscription")
            print("2. Check that ngrok is working: ngrok http 8765")
            print("3. Try in an incognito/private browser window")
            print("4. Check the scope configuration matches Claude's requirements")

        return False

if __name__ == "__main__":
    print("Claude Max OAuth Test (DEBUG)")
    print("=" * 80)
    print()

    # First check if config is loaded
    if not os.getenv("ACE_OAUTH_AUTH_URL"):
        print("Loading configuration...")

        # Try to load the config file
        config_file = Path("claude_max_oauth.env")
        if config_file.exists():
            print(f"Please run: source {config_file}")
            print("Then run this test again.")
        else:
            print("Please run: ./setup_claude_max_oauth.sh")
            print("Then: source claude_max_oauth.env")
            print("Then run this test again.")
        sys.exit(1)

    # Run the test
    if test_claude_max_oauth_debug():
        print()
        print("=" * 80)
        print("✅ SUCCESS!")
        print("=" * 80)
        print()
        print("You can now use ACE with your Claude Max subscription!")
        print("The OAuth token is cached and will be reused automatically.")
    else:
        print()
        print("=" * 80)
        print("Test failed. See errors above.")
        print("=" * 80)