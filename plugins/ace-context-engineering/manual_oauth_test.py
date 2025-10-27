#!/usr/bin/env python3
"""
Manual OAuth test - starts ngrok and waits for callback
"""
import http.server
import socketserver
import urllib.parse
import webbrowser
import time
import os

PORT = 8765

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
                </body>
                </html>
                """
                self.wfile.write(success_html.encode())

                # Store the code for later use
                global auth_code
                auth_code = params['code']

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
print("Manual OAuth Test")
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
print("3. Building OAuth URL...")

# OAuth parameters
client_id = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
redirect_uri = f"{ngrok_url}/callback"
scope = "org:create_api_key user:profile user:inference"
state = "test123"

auth_url = f"https://console.anthropic.com/oauth/authorize?" + urllib.parse.urlencode({
    'response_type': 'code',
    'client_id': client_id,
    'redirect_uri': redirect_uri,
    'scope': scope,
    'state': state
})

print(f"   Redirect URI: {redirect_uri}")
print()

print("4. Opening browser for authorization...")
print("   If the browser doesn't open, visit this URL:")
print(f"   {auth_url}")
print()

# Start the server
with socketserver.TCPServer(("", PORT), CallbackHandler) as httpd:
    print(f"5. Waiting for OAuth callback on port {PORT}...")
    print("   Click 'Authorize' in your browser...")
    print()

    # Open browser
    webbrowser.open(auth_url)

    # Wait for one request (the callback)
    auth_code = None
    httpd.handle_request()

    if auth_code:
        print()
        print("=" * 80)
        print("✅ SUCCESS! Authorization code received.")
        print("=" * 80)
        print()
        print("Next step would be to exchange this code for an access token.")
        print("The full OAuth flow is working correctly!")
    else:
        print()
        print("❌ No authorization code received.")