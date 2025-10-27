#!/bin/bash

# ACE OAuth Setup for Claude Max Subscription
# Uses browser-based OAuth flow with claude.ai

echo "=========================================="
echo "ACE OAuth Setup for Claude Max"
echo "=========================================="
echo ""
echo "This will configure ACE to use your Claude Max subscription"
echo "through browser-based OAuth authentication (no API key needed)."
echo ""

# Create OAuth configuration for Claude Max
cat > claude_max_oauth.env << 'EOF'
# Claude Max OAuth Configuration
# Uses official Claude.ai OAuth endpoints

# Official Claude OAuth endpoints
export ACE_OAUTH_AUTH_URL="https://console.anthropic.com/oauth/authorize"
export ACE_OAUTH_TOKEN_URL="https://api.anthropic.com/oauth/token"

# Official Claude Code client ID (publicly known)
export ACE_OAUTH_CLIENT_ID="9d1c250a-e61b-44d9-88ed-5944d1962f5e"

# Scopes for Claude Max access
export ACE_OAUTH_SCOPE="org:create_api_key+user:profile+user:inference"

# Claude API base URL (direct, no gateway needed)
export ACE_OAUTH_BASE_URL="https://api.anthropic.com"

# Optional: specific audience for Claude
export ACE_OAUTH_AUDIENCE="https://api.anthropic.com"

# Model to use with Max subscription
export ACE_OAUTH_MODEL="claude-3-5-sonnet-20241022"

# Local callback port (ngrok will tunnel this)
export ACE_OAUTH_REDIRECT_PORT="8765"

# Token cache location
export ACE_OAUTH_TOKEN_FILE="$HOME/.config/ace_claude_max_token.json"

# ngrok configuration (you'll need to set this)
# Get your token from: https://dashboard.ngrok.com/get-started/your-authtoken
export NGROK_AUTHTOKEN=""

# ngrok region
export ACE_OAUTH_NGROK_REGION="us"

# Anthropic API version
export ACE_OAUTH_VERSION="2023-06-01"
EOF

echo "✓ Configuration created: claude_max_oauth.env"
echo ""

# Check for ngrok
if command -v ngrok &> /dev/null; then
    echo "✓ ngrok is installed"

    # Check for authtoken
    if [ -f ~/.ngrok2/ngrok.yml ]; then
        echo "✓ ngrok config found"
    else
        echo ""
        echo "⚠️  ngrok needs configuration:"
        echo "   1. Get your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken"
        echo "   2. Run: ngrok config add-authtoken YOUR_TOKEN"
    fi
else
    echo "✗ ngrok not installed"
    echo ""
    echo "Please install ngrok first:"
    echo "   macOS:  brew install ngrok"
    echo "   Linux:  snap install ngrok"
    echo "   Other:  https://ngrok.com/download"
    echo ""
    echo "Then get your authtoken from:"
    echo "   https://dashboard.ngrok.com/get-started/your-authtoken"
fi

echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. SET UP NGROK (if not done):"
echo "   - Sign up at https://ngrok.com (free account works)"
echo "   - Get your authtoken from dashboard"
echo "   - Add it to claude_max_oauth.env:"
echo "     export NGROK_AUTHTOKEN=\"your-token-here\""
echo ""
echo "2. LOAD THE CONFIGURATION:"
echo "   source claude_max_oauth.env"
echo ""
echo "3. RUN THE TEST:"
echo "   python test_claude_max_oauth.py"
echo ""
echo "This will:"
echo "• Start ngrok tunnel to handle OAuth callback"
echo "• Open your browser to Claude login"
echo "• You login with your Claude Max account"
echo "• Automatically capture the OAuth token"
echo "• Save it for future use (no need to login again)"
echo ""