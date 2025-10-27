#!/usr/bin/env python3
"""
Direct token exchange - use existing authorization code
"""

import requests
import json
import time
from pathlib import Path

# Your authorization code from the latest session
auth_code = "zUuIrfpBn56Y3f2wo56WmS75yqHmB4E8201Z3pzWMf0UPJQ6"

# OAuth parameters from the latest session
client_id = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
redirect_uri = "http://localhost:8765/callback"
code_verifier = "J14wI7RpIMIedCjBD6jPCyxP.0d4JbAUDTg2UdgpANxcZI95XNh_wCn.P-71bR4"  # From the latest session
state = "uVFlcIYsnxbDpJZ9IPyvZleDJmzf981E92lMMf3yM6k"  # From callback URL

print("=" * 80)
print("Direct OAuth Token Exchange")
print("=" * 80)
print()

print(f"Authorization code: {auth_code[:20]}...")
print(f"Code verifier: {code_verifier[:20]}...")
print()

# Token exchange
print("Exchanging authorization code for access token...")

# Use the correct Claude Code endpoint
token_url = "https://console.anthropic.com/v1/oauth/token"

token_data = {
    'grant_type': 'authorization_code',
    'client_id': client_id,
    'code': auth_code,
    'redirect_uri': redirect_uri,
    'code_verifier': code_verifier,
    'state': state
}

print(f"Using endpoint: {token_url}")

try:
    response = requests.post(
        token_url,
        json=token_data,
        headers={"Content-Type": "application/json"},
        timeout=30
    )

    print(f"Response status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    print()

    if response.status_code == 200:
        token_info = response.json()
        print("✅ Access token received!")
        print(f"Token type: {token_info.get('token_type', 'unknown')}")
        print(f"Expires in: {token_info.get('expires_in', 'unknown')} seconds")
        print()

        # Save token to file
        print("Saving token to file...")
        token_file = Path.home() / ".config" / "ace_claude_max_token.json"
        token_file.parent.mkdir(parents=True, exist_ok=True)

        token_data_to_save = {
            "access_token": token_info.get("access_token"),
            "expires_at": time.time() + token_info.get("expires_in", 3600),
            "refresh_token": token_info.get("refresh_token"),
            "token_type": token_info.get("token_type", "Bearer")
        }

        token_file.write_text(json.dumps(token_data_to_save, indent=2))
        print(f"✅ Token saved to: {token_file}")
        print()

        print("=" * 80)
        print("✅ SUCCESS! OAuth flow completed.")
        print("=" * 80)
        print()

        # Show token info (first 20 chars only for security)
        print(f"Access token (first 20 chars): {token_info.get('access_token', '')[:20]}...")
        print()

        # Test the token
        print("Testing the token with a simple API call...")
        test_response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Authorization": f"Bearer {token_info.get('access_token')}",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 50,
                "messages": [
                    {"role": "user", "content": "Say 'OAuth working!' in exactly 2 words"}
                ]
            },
            timeout=30
        )

        if test_response.status_code == 200:
            result = test_response.json()
            message = result.get("content", [{}])[0].get("text", "")
            print(f"✅ API test successful!")
            print(f"Response: {message}")
        else:
            print(f"⚠ API test failed: HTTP {test_response.status_code}")
            print(f"Response: {test_response.text[:200]}")

    else:
        print(f"❌ Token exchange failed: HTTP {response.status_code}")
        print(f"Response body: {response.text[:1000]}")

except Exception as e:
    print(f"❌ Token exchange error: {e}")
    import traceback
    traceback.print_exc()
