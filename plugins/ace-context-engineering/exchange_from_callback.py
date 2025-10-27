#!/usr/bin/env python3
"""
Exchange OAuth authorization code from callback URL for access token
"""

import requests
import json
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Parse the callback URL from command line
if len(sys.argv) < 2:
    print("Usage: python3 exchange_from_callback.py <callback_url>")
    print("Example: python3 exchange_from_callback.py 'http://localhost:8765/callback?code=...&state=...'")
    sys.exit(1)

callback_url = sys.argv[1]

# Parse callback URL to extract code and state
parsed = urlparse(callback_url)
params = parse_qs(parsed.query)

auth_code = params.get('code', [None])[0]
state = params.get('state', [None])[0]

if not auth_code:
    print("❌ Error: No authorization code found in callback URL")
    sys.exit(1)

print("=" * 80)
print("OAuth Token Exchange from Callback URL")
print("=" * 80)
print()

# Now we need to load the code_verifier that was saved during the authorization
# Look for the latest run of manual_token_exchange.py or use a saved file
# For now, let's ask the user to provide it

print(f"Authorization code: {auth_code[:20]}...")
print(f"State: {state[:20]}..." if state else "State: (not provided)")
print()
print("To complete the token exchange, we need the code_verifier that was generated")
print("when the authorization URL was created.")
print()

# Try to find a saved code_verifier file
verifier_file = Path.home() / ".config" / "ace_oauth_verifier.txt"
if verifier_file.exists():
    code_verifier = verifier_file.read_text().strip()
    print(f"✅ Found saved code_verifier: {code_verifier[:20]}...")
else:
    print("❌ No saved code_verifier found.")
    print()
    print("Please provide the code_verifier that was displayed when you started the OAuth flow:")
    code_verifier = input("Code verifier: ").strip()

if not code_verifier:
    print("❌ Error: code_verifier is required")
    sys.exit(1)

print()

# OAuth configuration
client_id = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
redirect_uri = "http://localhost:8765/callback"
token_url = "https://console.anthropic.com/v1/oauth/token"

# Prepare token exchange request
token_data = {
    'grant_type': 'authorization_code',
    'client_id': client_id,
    'code': auth_code,
    'redirect_uri': redirect_uri,
    'code_verifier': code_verifier,
    'state': state
}

print("Exchanging authorization code for access token...")
print(f"Endpoint: {token_url}")
print()

try:
    response = requests.post(
        token_url,
        json=token_data,
        headers={"Content-Type": "application/json"},
        timeout=30
    )

    print(f"Response status: {response.status_code}")
    print()

    if response.status_code == 200:
        token_info = response.json()
        print("✅ Access token received!")
        print()

        # Save the token
        token_file = Path.home() / ".config" / "ace_claude_max_token.json"
        token_file.parent.mkdir(parents=True, exist_ok=True)

        with open(token_file, 'w') as f:
            json.dump(token_info, f, indent=2)

        print(f"Token saved to: {token_file}")
        print()
        print("Token details:")
        print(f"  Access token: {token_info.get('access_token', '')[:20]}...")
        print(f"  Token type: {token_info.get('token_type', 'N/A')}")
        print(f"  Expires in: {token_info.get('expires_in', 'N/A')} seconds")
        print(f"  Scope: {token_info.get('scope', 'N/A')}")

        if 'refresh_token' in token_info:
            print(f"  Refresh token: {token_info['refresh_token'][:20]}...")

        print()
        print("🎉 OAuth setup complete! You can now use your Claude Max subscription.")

    else:
        print(f"❌ Token exchange failed: HTTP {response.status_code}")
        print(f"Response body: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"❌ Request error: {e}")
    sys.exit(1)
