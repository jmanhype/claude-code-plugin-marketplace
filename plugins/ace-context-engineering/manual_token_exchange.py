#!/usr/bin/env python3
"""
Manual OAuth token exchange - bypasses the broken authorize button.

Instructions:
1. This script will give you an OAuth URL
2. Open it in your browser
3. Use browser DevTools to manually trigger the authorization
4. Paste the callback URL here
5. Script will exchange the code for a token
"""

import os
import sys
import secrets
import hashlib
import base64
import string
import urllib.parse
import requests
import json
import time
from pathlib import Path

def generate_code_verifier(length=64):
    """Generate a random code verifier for PKCE"""
    alphabet = string.ascii_letters + string.digits + "-._~"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_code_challenge(verifier):
    """Generate code challenge from verifier using SHA256"""
    digest = hashlib.sha256(verifier.encode('ascii')).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')

def main():
    print("=" * 80)
    print("Manual OAuth Token Exchange")
    print("=" * 80)
    print()

    # OAuth configuration
    client_id = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
    redirect_uri = "http://localhost:8765/callback"  # Simpler - no ngrok needed
    scope = "org:create_api_key user:profile user:inference"

    # Generate PKCE parameters
    print("1. Generating PKCE parameters...")
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    state = secrets.token_urlsafe(32)

    print(f"   Code verifier: {code_verifier[:20]}...")
    print(f"   Code challenge: {code_challenge[:20]}...")
    print(f"   State: {state[:20]}...")
    print()

    # Build OAuth URL
    print("2. Building OAuth URL...")
    auth_url = "https://console.anthropic.com/oauth/authorize?" + urllib.parse.urlencode({
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': scope,
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    })

    print()
    print("=" * 80)
    print("STEP 1: Opening OAuth URL in your browser...")
    print("=" * 80)
    print(auth_url)
    print()

    # Open the URL in the browser
    import webbrowser
    webbrowser.open(auth_url)
    print("✓ Browser opened!")
    print()

    print("=" * 80)
    print("STEP 2: Use Browser DevTools to trigger authorization:")
    print("=" * 80)
    print("1. Open the URL above in your browser")
    print("2. Open DevTools (F12 or Cmd+Option+I)")
    print("3. Go to Console tab")
    print("4. Paste and run this JavaScript:")
    print()
    print("   // Find the authorize form and submit it")
    print("   document.querySelector('form').submit();")
    print()
    print("   // OR find the button and force click")
    print("   document.querySelector('button[type=\"submit\"]')?.click();")
    print()
    print("   // OR make the API call directly")
    print("   fetch(window.location.href.replace('/authorize', '/v1/oauth/authorize'), {")
    print("     method: 'POST',")
    print("     headers: { 'Content-Type': 'application/x-www-form-urlencoded' },")
    print("     body: new URLSearchParams(Object.fromEntries(new URL(window.location.href).searchParams))")
    print("   }).then(r => r.json()).then(console.log)")
    print()
    print("=" * 80)
    print("STEP 3: After authorization, you'll be redirected to a non-working localhost URL")
    print("=" * 80)
    print("Copy the ENTIRE URL from your browser's address bar (it will look like:")
    print(f"http://localhost:8765/callback?code=XXXXX&state={state[:10]}...)")
    print()
    print("=" * 80)

    # Wait for user to paste the callback URL
    print()
    callback_url = input("Paste the callback URL here: ").strip()
    print()

    # Parse the callback URL
    print("3. Parsing callback URL...")
    try:
        parsed = urllib.parse.urlparse(callback_url)
        params = dict(urllib.parse.parse_qsl(parsed.query))

        if 'error' in params:
            print(f"   ❌ OAuth error: {params['error']}")
            print(f"   Description: {params.get('error_description', 'none')}")
            return False

        if 'code' not in params:
            print("   ❌ No authorization code found in URL")
            return False

        if params.get('state') != state:
            print("   ❌ State mismatch - possible CSRF attack!")
            return False

        auth_code = params['code']
        print(f"   ✓ Authorization code: {auth_code[:20]}...")
        print(f"   ✓ State verified: {state[:20]}...")
        print()

    except Exception as e:
        print(f"   ❌ Failed to parse URL: {e}")
        return False

    # Exchange code for token
    print("4. Exchanging authorization code for access token...")

    # Use the actual Claude Code token endpoint
    token_endpoints = [
        "https://console.anthropic.com/v1/oauth/token",  # From Claude Code source
        "https://api.anthropic.com/v1/oauth/token",
        "https://console.anthropic.com/oauth/token"
    ]

    token_data = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'code': auth_code,
        'redirect_uri': redirect_uri,
        'code_verifier': code_verifier
    }

    response = None
    for token_url in token_endpoints:
        try:
            print(f"   Trying endpoint: {token_url}")
            response = requests.post(token_url, data=token_data, timeout=30)
            print(f"   Response status: {response.status_code}")

            if response.status_code != 404:
                break  # Found a valid endpoint
        except Exception as e:
            print(f"   Error: {e}")
            continue

    if not response or response.status_code == 404:
        print(f"   ❌ All endpoints returned 404 - OAuth token endpoint not found")
        print(f"   This suggests Claude's OAuth is not publicly available yet")
        return False

    try:

        if response.status_code == 200:
            token_info = response.json()
            print("   ✅ Access token received!")
            print(f"   Token type: {token_info.get('token_type', 'unknown')}")
            print(f"   Expires in: {token_info.get('expires_in', 'unknown')} seconds")
            print()

            # Save token to file
            print("5. Saving token to file...")
            token_file = Path.home() / ".config" / "ace_claude_max_token.json"
            token_file.parent.mkdir(parents=True, exist_ok=True)

            token_data_to_save = {
                "access_token": token_info.get("access_token"),
                "expires_at": time.time() + token_info.get("expires_in", 3600),
                "refresh_token": token_info.get("refresh_token"),
                "token_type": token_info.get("token_type", "Bearer")
            }

            token_file.write_text(json.dumps(token_data_to_save, indent=2))
            print(f"   ✅ Token saved to: {token_file}")
            print()

            print("=" * 80)
            print("✅ SUCCESS! OAuth flow completed.")
            print("=" * 80)
            print()
            print("The access token has been saved and can be used for API calls.")
            print("You can now use your Claude Max subscription through OAuth!")
            print()

            # Test the token
            print("6. Testing the token with a simple API call...")
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
                        {"role": "user", "content": "Say 'OAuth is working!' in 3 words"}
                    ]
                },
                timeout=30
            )

            if test_response.status_code == 200:
                result = test_response.json()
                message = result.get("content", [{}])[0].get("text", "")
                print(f"   ✅ API test successful!")
                print(f"   Response: {message}")
            else:
                print(f"   ⚠ API test failed: HTTP {test_response.status_code}")
                print(f"   Response: {test_response.text[:200]}")

            return True

        else:
            print(f"   ❌ Token exchange failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"   ❌ Token exchange error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
