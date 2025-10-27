#!/bin/bash
# ACE OAuth Setup Script
# Source this file to set up your OAuth environment: source oauth_setup.sh

echo "=================================="
echo "ACE OAuth Environment Setup"
echo "=================================="

# Check if we're being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "❌ This script must be sourced, not executed:"
    echo "   source oauth_setup.sh"
    echo "   or"
    echo "   . oauth_setup.sh"
    exit 1
fi

# Function to prompt for value with default
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"

    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " value
        value="${value:-$default}"
    else
        read -p "$prompt: " value
    fi

    export "$var_name=$value"
    echo "   ✓ $var_name set"
}

echo ""
echo "This script will help you set up the required OAuth environment variables."
echo "Press Enter to use defaults where available."
echo ""

# Check for existing values
echo "Checking existing configuration..."
if [ -n "$ACE_OAUTH_BASE_URL" ]; then
    echo "   Found existing OAuth configuration"
    read -p "Do you want to reconfigure? (y/N): " reconfigure
    if [ "$reconfigure" != "y" ] && [ "$reconfigure" != "Y" ]; then
        echo "   Keeping existing configuration"
        return 0
    fi
fi

echo ""
echo "1. OAuth Gateway Configuration"
echo "------------------------------"

# Get OAuth gateway details
prompt_with_default "OAuth Authorization URL" "" "ACE_OAUTH_AUTH_URL"
prompt_with_default "OAuth Token URL" "" "ACE_OAUTH_TOKEN_URL"
prompt_with_default "OAuth Client ID" "" "ACE_OAUTH_CLIENT_ID"
prompt_with_default "OAuth Scope" "anthropic:messages:write" "ACE_OAUTH_SCOPE"
prompt_with_default "OAuth Base URL (gateway URL)" "" "ACE_OAUTH_BASE_URL"

echo ""
echo "2. Optional OAuth Settings"
echo "--------------------------"

prompt_with_default "OAuth Audience (leave blank if not required)" "" "ACE_OAUTH_AUDIENCE"
prompt_with_default "OAuth Redirect Port" "8765" "ACE_OAUTH_REDIRECT_PORT"
prompt_with_default "ngrok Region" "us" "ACE_OAUTH_NGROK_REGION"
prompt_with_default "Claude Model" "claude-3-5-sonnet-20241022" "ACE_OAUTH_MODEL"
prompt_with_default "Token Cache File" "$HOME/.config/ace_oauth_token.json" "ACE_OAUTH_TOKEN_FILE"

echo ""
echo "3. ngrok Configuration"
echo "----------------------"

# Check if ngrok is installed
if command -v ngrok &> /dev/null; then
    echo "   ✓ ngrok is installed"

    # Check for authtoken
    if [ -z "$NGROK_AUTHTOKEN" ]; then
        echo ""
        echo "   ⚠️  NGROK_AUTHTOKEN not set"
        echo "   Get your token from: https://dashboard.ngrok.com/get-started/your-authtoken"
        prompt_with_default "ngrok Authtoken" "" "NGROK_AUTHTOKEN"
    else
        echo "   ✓ NGROK_AUTHTOKEN is set"
    fi
else
    echo "   ✗ ngrok not found"
    echo ""
    echo "   Please install ngrok:"
    echo "      macOS:  brew install ngrok"
    echo "      Linux:  snap install ngrok"
    echo "      Other:  https://ngrok.com/download"
    echo ""
    echo "   Then get your authtoken from:"
    echo "      https://dashboard.ngrok.com/get-started/your-authtoken"
    prompt_with_default "ngrok Authtoken (set even if not installed yet)" "" "NGROK_AUTHTOKEN"
fi

echo ""
echo "=================================="
echo "Configuration Summary"
echo "=================================="
echo "Auth URL:      $ACE_OAUTH_AUTH_URL"
echo "Token URL:     $ACE_OAUTH_TOKEN_URL"
echo "Client ID:     $ACE_OAUTH_CLIENT_ID"
echo "Scope:         $ACE_OAUTH_SCOPE"
echo "Base URL:      $ACE_OAUTH_BASE_URL"
echo "Model:         $ACE_OAUTH_MODEL"
echo "ngrok:         ${NGROK_AUTHTOKEN:0:10}..."
echo ""

# Save to file for persistence
CONFIG_FILE="$HOME/.ace_oauth_env"
echo "Saving configuration to $CONFIG_FILE..."

cat > "$CONFIG_FILE" << EOF
# ACE OAuth Configuration
# Generated on $(date)

export ACE_OAUTH_AUTH_URL="$ACE_OAUTH_AUTH_URL"
export ACE_OAUTH_TOKEN_URL="$ACE_OAUTH_TOKEN_URL"
export ACE_OAUTH_CLIENT_ID="$ACE_OAUTH_CLIENT_ID"
export ACE_OAUTH_SCOPE="$ACE_OAUTH_SCOPE"
export ACE_OAUTH_BASE_URL="$ACE_OAUTH_BASE_URL"
export ACE_OAUTH_AUDIENCE="$ACE_OAUTH_AUDIENCE"
export ACE_OAUTH_REDIRECT_PORT="$ACE_OAUTH_REDIRECT_PORT"
export ACE_OAUTH_NGROK_REGION="$ACE_OAUTH_NGROK_REGION"
export ACE_OAUTH_MODEL="$ACE_OAUTH_MODEL"
export ACE_OAUTH_TOKEN_FILE="$ACE_OAUTH_TOKEN_FILE"
export NGROK_AUTHTOKEN="$NGROK_AUTHTOKEN"
EOF

echo "   ✓ Configuration saved"
echo ""
echo "To load this configuration in the future:"
echo "   source $CONFIG_FILE"
echo ""
echo "To test the OAuth flow:"
echo "   python test_oauth_flow.py"
echo ""
echo "✅ Setup complete!"