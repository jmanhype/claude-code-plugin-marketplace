#!/bin/bash
#
# Setup Claude Code using the claude-code-login tool
#

set -e

CLAUDE_LOGIN_DIR="$HOME/claude-code-login"
ACE_DIR="$HOME/claude-code-plugin-marketplace/plugins/ace-context-engineering"
CONFIG_DIR="$HOME/.config"

echo "=" | tr '=' '=' | head -c 80; echo
echo "Claude Code OAuth Setup (using claude-code-login)"
echo "=" | tr '=' '=' | head -c 80; echo
echo

# Check if claude-code-login exists
if [ ! -d "$CLAUDE_LOGIN_DIR" ]; then
    echo "❌ claude-code-login not found at: $CLAUDE_LOGIN_DIR"
    echo "   Cloning repository..."
    cd ~ && git clone https://github.com/grll/claude-code-login.git
    cd "$CLAUDE_LOGIN_DIR" && bun install
fi

cd "$CLAUDE_LOGIN_DIR"

# Check if credentials already exist
if [ -f "credentials.json" ]; then
    echo "✓ Existing credentials found"
    echo
    read -p "Do you want to use existing credentials? (y/n): " use_existing

    if [ "$use_existing" = "y" ] || [ "$use_existing" = "Y" ]; then
        echo "Using existing credentials..."
    else
        echo "Generating new login..."
        rm -f credentials.json claude_oauth_state.json

        echo
        echo "Step 1: Open this URL in your browser:"
        echo "=" | tr '=' '-' | head -c 80; echo
        bun run index.ts
        echo "=" | tr '=' '-' | head -c 80; echo
        echo
        echo "Step 2: After authorizing, copy the 'code' parameter from the callback URL"
        echo "        (it will look like: https://console.anthropic.com/oauth/code/callback?code=XXXXX)"
        echo
        read -p "Paste the authorization code here: " auth_code

        # Exchange code for tokens
        echo
        echo "Exchanging code for tokens..."
        bun run index.ts "$auth_code"
    fi
else
    echo "No existing credentials found. Starting fresh..."
    echo
    echo "Step 1: Open this URL in your browser:"
    echo "=" | tr '=' '-' | head -c 80; echo
    bun run index.ts
    echo "=" | tr '=' '-' | head -c 80; echo
    echo
    echo "Step 2: After authorizing, copy the 'code' parameter from the callback URL"
    echo "        (it will look like: https://console.anthropic.com/oauth/code/callback?code=XXXXX)"
    echo
    read -p "Paste the authorization code here: " auth_code

    # Exchange code for tokens
    echo
    echo "Exchanging code for tokens..."
    bun run index.ts "$auth_code"
fi

# Check if credentials were created
if [ ! -f "credentials.json" ]; then
    echo "❌ Failed to create credentials"
    exit 1
fi

echo
echo "✅ OAuth credentials obtained!"
echo

# Now create API key from OAuth token
echo "Creating API key from OAuth token..."
ACCESS_TOKEN=$(jq -r '.claudeAiOauth.accessToken' credentials.json)

# Use the Claude CLI endpoint to create an API key
API_KEY_RESPONSE=$(curl -s -X POST "https://api.anthropic.com/api/oauth/claude_cli/create_api_key" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json")

# Extract API key
API_KEY=$(echo "$API_KEY_RESPONSE" | jq -r '.raw_key // empty')

if [ -z "$API_KEY" ]; then
    echo "❌ Failed to create API key"
    echo "Response: $API_KEY_RESPONSE"
    exit 1
fi

echo "✅ API key created: ${API_KEY:0:30}..."

# Save to ACE configuration
mkdir -p "$CONFIG_DIR"

# Copy credentials to .config
cp credentials.json "$CONFIG_DIR/claude_code_credentials.json"

# Save API key
echo "$API_KEY" > "$CONFIG_DIR/ace_claude_max_api_key.txt"

# Create environment configuration
cat > "$CONFIG_DIR/ace_claude_code.env" <<EOF
# Claude Code OAuth Configuration
# Generated: $(date)
# Source: claude-code-login tool

# Claude API Key (created from OAuth token)
export ANTHROPIC_API_KEY="$API_KEY"

# OAuth credentials file
export CLAUDE_CODE_CREDENTIALS="$CONFIG_DIR/claude_code_credentials.json"

# Claude API configuration
export ACE_OAUTH_MODEL="claude-3-5-sonnet-20241022"
export ACE_OAUTH_VERSION="2023-06-01"
export ACE_OAUTH_BASE_URL="https://api.anthropic.com"
EOF

echo
echo "=" | tr '=' '=' | head -c 80; echo
echo "✅ Setup Complete!"
echo "=" | tr '=' '=' | head -c 80; echo
echo
echo "Configuration saved to:"
echo "  • $CONFIG_DIR/ace_claude_code.env"
echo "  • $CONFIG_DIR/claude_code_credentials.json"
echo "  • $CONFIG_DIR/ace_claude_max_api_key.txt"
echo
echo "To use Claude Code with ACE, run:"
echo "  source ~/.config/ace_claude_code.env"
echo
echo "Or add to your shell profile:"
echo "  echo 'source ~/.config/ace_claude_code.env' >> ~/.zshrc"
echo
