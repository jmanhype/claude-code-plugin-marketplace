#!/usr/bin/env python3
"""
Manual OAuth test with PKCE - starts ngrok and waits for callback
"""
import http.server
import socketserver
import urllib.parse
import webbrowser
import time
import os
import secrets
import hashlib
import base64
import string

PORT = 8765

def generate_code_verifier(length=64):
    """Generate a random code verifier for PKCE"""
    alphabet = string.ascii_letters + string.digits + "-._~"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_code_challenge(verifier):
    """Generate code challenge from verifier using SHA256"""
    digest = hashlib.sha256(verifier.encode('ascii')).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')

class CallbackHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Handle OAuth callback"""
        print(f"\n📥 Received callback: {self.path}")

        # Parse the callback URL
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == '/callback':
            params = dict(urllib.parse.parse_qsl(parsed.query))

            if 'code' in params:
                print(f"✅ Authorization code received: {params['code'][:20]}...")
                print(f"   State: {params.get('state', 'none')}")

                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                success_html = """
                <html>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1>✅ Authorization Successful!</h1>
                    <p>You can close this tab and return to the terminal.</p>
                    <p>The authorization code has been received.</p>
                    <p style="margin-top: 30px; color: #666;">
                        The script will now exchange this code for an access token...
                    </p>
                </body>
                </html>
                """
                self.wfile.write(success_html.encode())

                # Store the code for later use
                global auth_code, state_received
                auth_code = params['code']
                state_received = params.get('state')

            elif 'error' in params:
                print(f"❌ OAuth error: {params['error']}")
                print(f"   Description: {params.get('error_description', 'none')}")

                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                error_html = f"""
                <html>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1>❌ Authorization Failed</h1>
                    <p>Error: {params['error']}</p>
                    <p>{params.get('error_description', '')}</p>
                </body>
                </html>
                """
                self.wfile.write(error_html.encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

    def log_message(self, format, *args):
        """Override to reduce noise"""
        return

print("=" * 80)
print("Manual OAuth Test with PKCE")
print("=" * 80)
print()

print("1. Starting local callback server on port 8765...")
print()

# Get the ngrok URL
print("2. Getting ngrok tunnel URL...")
print("   (Make sure ngrok is running: ngrok http 8765)")
print()

# Try to get ngrok URL
import requests
try:
    response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
    tunnels = response.json()

    ngrok_url = None
    for tunnel in tunnels.get('tunnels', []):
        if tunnel.get('proto') == 'https':
            ngrok_url = tunnel['public_url']
            break

    if ngrok_url:
        print(f"✅ Found ngrok tunnel: {ngrok_url}")
    else:
        print("❌ No HTTPS tunnel found. Please run: ngrok http 8765")
        exit(1)

except Exception as e:
    print("❌ Cannot connect to ngrok. Please run in another terminal:")
    print("   ngrok http 8765")
    print()
    print("Then run this script again.")
    exit(1)

print()
print("3. Generating PKCE parameters...")

# Generate PKCE parameters
code_verifier = generate_code_verifier()
code_challenge = generate_code_challenge(code_verifier)
state = secrets.token_urlsafe(32)

print(f"   Code verifier: {code_verifier[:20]}...")
print(f"   Code challenge: {code_challenge[:20]}...")
print(f"   State: {state[:20]}...")

print()
print("4. Building OAuth URL with PKCE...")

# OAuth parameters
client_id = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
redirect_uri = f"{ngrok_url}/callback"
scope = "org:create_api_key user:profile user:inference"

auth_url = f"https://console.anthropic.com/oauth/authorize?" + urllib.parse.urlencode({
    'response_type': 'code',
    'client_id': client_id,
    'redirect_uri': redirect_uri,
    'scope': scope,
    'state': state,
    'code_challenge': code_challenge,
    'code_challenge_method': 'S256'
})

print(f"   Redirect URI: {redirect_uri}")
print()

print("5. Opening browser for authorization...")
print("   If the browser doesn't open, visit this URL:")
print(f"   {auth_url}")
print()

# Start the server
with socketserver.TCPServer(("", PORT), CallbackHandler) as httpd:
    print(f"6. Waiting for OAuth callback on port {PORT}...")
    print("   Click 'Authorize' in your browser...")
    print()

    # Open browser
    webbrowser.open(auth_url)

    # Wait for one request (the callback)
    auth_code = None
    state_received = None
    httpd.handle_request()

    if auth_code:
        print()
        print("7. Verifying state parameter...")
        if state_received == state:
            print("   ✅ State matches - no CSRF attack")
        else:
            print("   ❌ State mismatch - possible CSRF attack!")
            print(f"   Expected: {state}")
            print(f"   Received: {state_received}")

        print()
        print("8. Exchanging authorization code for access token...")

        # Exchange code for token
        token_url = "https://api.anthropic.com/oauth/token"
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'code': auth_code,
            'redirect_uri': redirect_uri,
            'code_verifier': code_verifier
        }

        try:
            token_response = requests.post(token_url, data=token_data, timeout=30)

            if token_response.status_code == 200:
                token_info = token_response.json()
                print("   ✅ Access token received!")
                print(f"   Token type: {token_info.get('token_type', 'unknown')}")
                print(f"   Expires in: {token_info.get('expires_in', 'unknown')} seconds")

                # Save token to file
                import json
                from pathlib import Path

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
                print("✅ SUCCESS! Full OAuth flow completed.")
                print("=" * 80)
                print()
                print("The access token has been saved and can be used for API calls.")
                print("You can now use your Claude Max subscription through OAuth!")

            else:
                print(f"   ❌ Token exchange failed: HTTP {token_response.status_code}")
                print(f"   Response: {token_response.text[:500]}")

        except Exception as e:
            print(f"   ❌ Token exchange error: {e}")

    else:
        print()
        print("❌ No authorization code received.")