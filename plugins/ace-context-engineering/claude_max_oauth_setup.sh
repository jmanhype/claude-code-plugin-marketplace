#!/bin/bash
#
# Configure ACE to use your Claude Max OAuth token
#

# Read the token file
TOKEN_FILE="$HOME/.config/ace_claude_max_token.json"
API_KEY_FILE="$HOME/.config/ace_claude_max_api_key.txt"

if [ ! -f "$TOKEN_FILE" ]; then
    echo "❌ OAuth token not found at: $TOKEN_FILE"
    echo "Please run the OAuth setup first."
    exit 1
fi

if [ ! -f "$API_KEY_FILE" ]; then
    echo "❌ API key not found at: $API_KEY_FILE"
    echo "Please run the OAuth setup to create an API key."
    exit 1
fi

# Extract access token
ACCESS_TOKEN=$(python3 -c "import json; print(json.load(open('$TOKEN_FILE'))['access_token'])")
API_KEY=$(cat "$API_KEY_FILE")

# Export environment variables for ACE
cat > "$HOME/.config/ace_claude_max.env" <<EOF
# Claude Max OAuth Configuration
# Generated: $(date)

# Use the API key directly (Claude API doesn't support OAuth Bearer tokens directly)
export ANTHROPIC_API_KEY="$API_KEY"

# For future: OAuth configuration (not currently used by Anthropic API)
export ACE_OAUTH_ACCESS_TOKEN="$ACCESS_TOKEN"
export ACE_OAUTH_TOKEN_FILE="$TOKEN_FILE"

# Claude API configuration
export ACE_OAUTH_MODEL="claude-3-5-sonnet-20241022"
export ACE_OAUTH_VERSION="2023-06-01"
export ACE_OAUTH_BASE_URL="https://api.anthropic.com"

# Note: Anthropic API currently requires x-api-key header, not OAuth Bearer tokens
# We're using the API key created from the OAuth token
EOF

echo "✅ Configuration saved to: $HOME/.config/ace_claude_max.env"
echo ""
echo "To use your Claude Max subscription with ACE, run:"
echo "  source ~/.config/ace_claude_max.env"
echo ""
echo "Or add this to your shell profile:"
echo "  echo 'source ~/.config/ace_claude_max.env' >> ~/.bashrc"
echo "  echo 'source ~/.config/ace_claude_max.env' >> ~/.zshrc"
