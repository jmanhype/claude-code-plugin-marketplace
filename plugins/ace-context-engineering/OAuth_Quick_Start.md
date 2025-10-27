# ACE OAuth Quick Start Guide

## Prerequisites

1. **ngrok installed and configured**
   ```bash
   # Install ngrok
   brew install ngrok  # macOS

   # Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
   ngrok config add-authtoken YOUR_AUTHTOKEN
   ```

2. **OAuth Gateway Running**
   - You need an OAuth gateway that fronts the Anthropic API
   - The gateway must translate `Authorization: Bearer` → `x-api-key`

## Quick Setup

### Option 1: Interactive Setup (Recommended)
```bash
cd plugins/ace-context-engineering
source oauth_setup.sh
```

This will prompt you for all required values and save them to `~/.ace_oauth_env`

### Option 2: Manual Setup
```bash
# Required variables
export ACE_OAUTH_AUTH_URL="https://your-gateway.com/oauth/authorize"
export ACE_OAUTH_TOKEN_URL="https://your-gateway.com/oauth/token"
export ACE_OAUTH_CLIENT_ID="your-client-id"
export ACE_OAUTH_SCOPE="anthropic:messages:write"
export ACE_OAUTH_BASE_URL="https://your-gateway.com"
export NGROK_AUTHTOKEN="your-ngrok-token"

# Optional variables
export ACE_OAUTH_MODEL="claude-3-5-sonnet-20241022"
export ACE_OAUTH_REDIRECT_PORT="8765"
```

## Test Your Setup

```bash
# Run the test script
python test_oauth_flow.py
```

This will:
1. Check all environment variables
2. Verify ngrok is working
3. Start the OAuth flow (opens browser)
4. Exchange code for token
5. Make a test API call to Claude

## How the Flow Works

1. **You run ACE** → ACE needs to call Claude
2. **ACE starts ngrok** → Creates public HTTPS tunnel to localhost:8765
3. **ACE opens browser** → Navigates to your OAuth gateway login
4. **You authorize** → Grant ACE permission to use your Claude access
5. **Gateway redirects** → Sends auth code to ngrok URL
6. **ngrok forwards** → Delivers code to ACE's local server
7. **ACE exchanges** → Trades auth code for access token
8. **Token cached** → Saved to `~/.config/ace_oauth_token.json`
9. **ACE calls Claude** → Uses token for API requests

## Troubleshooting

### "ngrok not found"
```bash
# Install ngrok
brew install ngrok
# Or download from https://ngrok.com/download
```

### "Failed to obtain ngrok public URL"
```bash
# Check ngrok is authenticated
ngrok config add-authtoken YOUR_TOKEN

# Test ngrok manually
ngrok http 8765
```

### "Missing required OAuth environment variables"
```bash
# Run the setup script
source oauth_setup.sh

# Or load saved config
source ~/.ace_oauth_env
```

### "OAuth2 state mismatch"
- Browser cookies might be interfering
- Try in incognito/private window
- Check your gateway allows localhost redirects

### "Token endpoint error: HTTP 401"
- Verify your client_id is correct
- Check your client_secret (if required)
- Ensure your gateway is running

### "Claude call failed: HTTP 403"
- Token might not have correct scopes
- Gateway might not be forwarding correctly
- Check ACE_OAUTH_BASE_URL points to gateway, not Anthropic directly

## Test Without Real Gateway

To test the flow without a real OAuth gateway:

```python
# In test_oauth_flow.py, you can mock responses
import json
from unittest.mock import Mock

# Mock the OAuth client
mock_client = Mock()
mock_client.complete.return_value = Mock(text="OAuth is working!")

# Test with mock
print("Testing with mock client...")
response = mock_client.complete("test")
print(f"Mock response: {response.text}")
```

## Security Notes

1. **Token Storage**: Token cached at `~/.config/ace_oauth_token.json`
   - File permissions should be 600 (user read/write only)
   - Token expires after 1 hour by default

2. **ngrok Security**:
   - Uses authenticated tunnels (requires NGROK_AUTHTOKEN)
   - Tunnel closes after OAuth callback received
   - Only accepts expected OAuth parameters

3. **Client Credentials**:
   - Never commit client_id or secrets to git
   - Use environment variables or secure config files
   - Rotate credentials periodically

## Next Steps

Once OAuth is working:

1. **Run the full ACE pipeline**:
   ```bash
   MAX_SAMPLES=1 MAX_EPOCHS=1 python -u benchmarks/run_offline_adaptation.py
   ```

2. **Test skill invocation**:
   ```python
   from claude_code_skill_invoker import invoke_skill

   code = invoke_skill(
       "generate-appworld-code",
       '{"instruction": "Find my most liked song on Spotify"}'
   )
   print(code)
   ```

3. **Monitor token usage**:
   ```bash
   # Check if token is cached
   cat ~/.config/ace_oauth_token.json | jq .expires_at

   # Clear cached token to force re-auth
   rm ~/.config/ace_oauth_token.json
   ```

## Common Gateway Requirements

Your OAuth gateway needs to:

1. Support Authorization Code flow with PKCE
2. Accept localhost redirect URIs
3. Translate `Authorization: Bearer` → `x-api-key`
4. Forward to Anthropic's Messages API
5. Return tokens with reasonable expiry (1-24 hours)

## Example Gateway Config

If you're building your own gateway:

```javascript
// Minimal Express gateway example
app.post('/oauth/token', (req, res) => {
  // Validate client_id, code, code_verifier
  if (validateOAuth(req.body)) {
    res.json({
      access_token: generateToken(),
      token_type: 'Bearer',
      expires_in: 3600
    });
  }
});

app.post('/v1/messages', authenticateBearer, (req, res) => {
  // Forward to Anthropic with API key
  anthropic.messages.create({
    ...req.body,
    headers: { 'x-api-key': process.env.ANTHROPIC_API_KEY }
  }).then(res.json);
});
```