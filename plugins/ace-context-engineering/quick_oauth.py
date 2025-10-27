#!/usr/bin/env python3
"""
Quick OAuth flow - generates URL, saves verifier, and waits for callback
"""

import secrets
import hashlib
import base64
import string
import urllib.parse
import webbrowser
from pathlib import Path

def generate_code_verifier(length=64):
    """Generate a random code verifier for PKCE"""
    alphabet = string.ascii_letters + string.digits + "-._~"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_code_challenge(verifier):
    """Generate code challenge from verifier using SHA256"""
    digest = hashlib.sha256(verifier.encode('ascii')).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')

# OAuth configuration
client_id = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
redirect_uri = "http://localhost:8765/callback"
scope = "org:create_api_key user:profile user:inference"

# Generate PKCE parameters
code_verifier = generate_code_verifier()
code_challenge = generate_code_challenge(code_verifier)
state = secrets.token_urlsafe(32)

# Save code_verifier for exchange script
verifier_file = Path.home() / ".config" / "ace_oauth_verifier.txt"
verifier_file.parent.mkdir(parents=True, exist_ok=True)
verifier_file.write_text(code_verifier)

print("=" * 80)
print("Quick OAuth Setup")
print("=" * 80)
print()
print(f"✓ Code verifier saved to: {verifier_file}")
print(f"  {code_verifier}")
print()

# Build OAuth URL
auth_url = "https://console.anthropic.com/oauth/authorize?" + urllib.parse.urlencode({
    'response_type': 'code',
    'client_id': client_id,
    'redirect_uri': redirect_uri,
    'scope': scope,
    'state': state,
    'code_challenge': code_challenge,
    'code_challenge_method': 'S256'
})

print("Opening OAuth URL in browser...")
print(auth_url)
print()

webbrowser.open(auth_url)

print("=" * 80)
print("Next steps:")
print("=" * 80)
print("1. In your browser, open DevTools (F12)")
print("2. Go to Console tab")
print("3. Paste this JavaScript to trigger authorization:")
print()
print("   document.querySelector('form').submit();")
print()
print("4. Copy the callback URL from your browser")
print("5. Run: python3 exchange_from_callback.py '<callback_url>'")
print()
print("=" * 80)
