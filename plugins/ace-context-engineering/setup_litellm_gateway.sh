#!/bin/bash

# ACE OAuth Gateway Setup using LiteLLM
# This sets up a local OAuth-compatible gateway for Anthropic Claude

echo "======================================"
echo "ACE OAuth Gateway Setup with LiteLLM"
echo "======================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Install LiteLLM if not present
echo "1. Installing LiteLLM..."
if ! pip show litellm &> /dev/null; then
    pip install litellm
    echo "   ✓ LiteLLM installed"
else
    echo "   ✓ LiteLLM already installed"
fi

# Create LiteLLM config
echo ""
echo "2. Creating LiteLLM configuration..."

cat > litellm_config.yaml << 'EOF'
model_list:
  - model_name: claude-3-5-sonnet
    litellm_params:
      model: anthropic/claude-3-5-sonnet-20241022
      api_key: os.environ/ANTHROPIC_API_KEY

  - model_name: claude-3-opus
    litellm_params:
      model: anthropic/claude-3-opus-20240229
      api_key: os.environ/ANTHROPIC_API_KEY

litellm_settings:
  drop_params: True
  success_callback: ["langfuse"]

general_settings:
  master_key: "sk-ace-oauth-gateway-key-123456789"
  database_url: "sqlite:///./litellm.db"

  # OAuth-like authentication
  custom_auth: true

  # Enable CORS for browser-based OAuth flows
  cors:
    allow_origins: ["http://localhost:*", "https://*.ngrok.io"]
    allow_methods: ["GET", "POST", "OPTIONS"]
    allow_headers: ["Authorization", "Content-Type"]
EOF

echo "   ✓ Configuration created: litellm_config.yaml"

# Create OAuth environment setup
echo ""
echo "3. Setting up OAuth environment variables..."

cat > ace_oauth_litellm.env << 'EOF'
# ACE OAuth Configuration for LiteLLM Gateway

# LiteLLM acts as our OAuth gateway
export ACE_OAUTH_AUTH_URL="http://localhost:4000/oauth/authorize"
export ACE_OAUTH_TOKEN_URL="http://localhost:4000/key/generate"
export ACE_OAUTH_CLIENT_ID="ace-client"
export ACE_OAUTH_SCOPE="anthropic:messages:write"
export ACE_OAUTH_BASE_URL="http://localhost:4000"

# LiteLLM master key acts as our OAuth secret
export ACE_OAUTH_CLIENT_SECRET="sk-ace-oauth-gateway-key-123456789"

# Model configuration
export ACE_OAUTH_MODEL="claude-3-5-sonnet"

# Port configuration
export ACE_OAUTH_REDIRECT_PORT="8765"
export LITELLM_PORT="4000"

# Your actual Anthropic API key (required)
# REPLACE THIS WITH YOUR ACTUAL KEY
export ANTHROPIC_API_KEY="sk-ant-api03-YOUR-ACTUAL-KEY-HERE"

# For ngrok (if you have it)
export NGROK_AUTHTOKEN="your-ngrok-token-if-you-have-one"
EOF

echo "   ✓ Environment file created: ace_oauth_litellm.env"

# Create startup script
echo ""
echo "4. Creating startup script..."

cat > start_ace_gateway.sh << 'EOF'
#!/bin/bash

echo "Starting ACE OAuth Gateway (LiteLLM)..."

# Load environment
if [ -f ace_oauth_litellm.env ]; then
    source ace_oauth_litellm.env
fi

# Check for Anthropic API key
if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" == "sk-ant-api03-YOUR-ACTUAL-KEY-HERE" ]; then
    echo "❌ Please set your actual ANTHROPIC_API_KEY in ace_oauth_litellm.env"
    exit 1
fi

# Start LiteLLM proxy
echo "Starting LiteLLM proxy on port 4000..."
echo "Dashboard will be available at: http://localhost:4000/ui"
echo ""

litellm --config litellm_config.yaml --port 4000 --detailed_debug
EOF

chmod +x start_ace_gateway.sh

echo "   ✓ Startup script created: start_ace_gateway.sh"

# Create simplified OAuth test
echo ""
echo "5. Creating simplified test script..."

cat > test_litellm_oauth.py << 'EOF'
#!/usr/bin/env python3
"""Test LiteLLM OAuth Gateway for ACE"""

import os
import sys
import json
import requests
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / "benchmarks" / "utils"))

def test_direct_litellm():
    """Test direct connection to LiteLLM (simpler than full OAuth)"""

    print("=" * 60)
    print("Testing LiteLLM Gateway Connection")
    print("=" * 60)

    # Check if LiteLLM is running
    try:
        response = requests.get("http://localhost:4000/health", timeout=2)
        if response.status_code == 200:
            print("✓ LiteLLM is running")
        else:
            print("✗ LiteLLM health check failed")
            return False
    except:
        print("✗ LiteLLM is not running. Start it with: ./start_ace_gateway.sh")
        return False

    # Get a test key from LiteLLM
    print("\n2. Getting access token from LiteLLM...")

    master_key = "sk-ace-oauth-gateway-key-123456789"

    try:
        # LiteLLM accepts the master key directly
        headers = {
            "Authorization": f"Bearer {master_key}",
            "Content-Type": "application/json"
        }

        # Test the gateway with a simple completion
        payload = {
            "model": "claude-3-5-sonnet",
            "messages": [
                {"role": "user", "content": "Say 'Gateway working!' in exactly 3 words."}
            ],
            "max_tokens": 50
        }

        response = requests.post(
            "http://localhost:4000/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✓ Gateway response: {content}")
            return True
        else:
            print(f"✗ Gateway error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_ace_integration():
    """Test ACE skill invocation through LiteLLM"""

    print("\n" + "=" * 60)
    print("Testing ACE Integration with LiteLLM")
    print("=" * 60)

    # Set up environment for ACE
    os.environ["ACE_OAUTH_BASE_URL"] = "http://localhost:4000"
    os.environ["ACE_OAUTH_AUTH_URL"] = "http://localhost:4000/oauth/authorize"
    os.environ["ACE_OAUTH_TOKEN_URL"] = "http://localhost:4000/key/generate"
    os.environ["ACE_OAUTH_CLIENT_ID"] = "ace-client"
    os.environ["ACE_OAUTH_CLIENT_SECRET"] = "sk-ace-oauth-gateway-key-123456789"
    os.environ["ACE_OAUTH_MODEL"] = "claude-3-5-sonnet"

    # For this test, we'll bypass the full OAuth flow and use direct auth
    os.environ["ANTHROPIC_BASE_URL"] = "http://localhost:4000"
    os.environ["ANTHROPIC_AUTH_TOKEN"] = "sk-ace-oauth-gateway-key-123456789"

    try:
        from claude_code_skill_invoker import invoke_skill

        test_prompt = json.dumps({
            "instruction": "Print hello world",
            "apps": ["general"]
        })

        print("\nInvoking skill through ACE...")
        response = invoke_skill("generate-appworld-code", test_prompt)

        print(f"✓ Skill invocation successful!")
        print(f"Response preview: {response[:200]}...")
        return True

    except ImportError:
        print("✗ ACE modules not found. This is expected if running standalone.")
        return False
    except Exception as e:
        print(f"✗ ACE integration error: {e}")
        return False

if __name__ == "__main__":
    print("\nACE-LiteLLM Gateway Test\n")

    # Test direct connection
    if test_direct_litellm():
        print("\n✅ LiteLLM gateway is working!")

        # Try ACE integration
        test_ace_integration()
    else:
        print("\n❌ Please start the gateway first:")
        print("   1. Edit ace_oauth_litellm.env and add your ANTHROPIC_API_KEY")
        print("   2. Run: ./start_ace_gateway.sh")
        print("   3. Run this test again")
EOF

chmod +x test_litellm_oauth.py

echo "   ✓ Test script created: test_litellm_oauth.py"

# Final instructions
echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo ""
echo "1. ADD YOUR ANTHROPIC API KEY:"
echo "   Edit ace_oauth_litellm.env and replace:"
echo "   sk-ant-api03-YOUR-ACTUAL-KEY-HERE"
echo "   with your actual Anthropic API key"
echo ""
echo "2. START THE GATEWAY:"
echo "   ./start_ace_gateway.sh"
echo ""
echo "3. TEST THE CONNECTION:"
echo "   python test_litellm_oauth.py"
echo ""
echo "The LiteLLM gateway will:"
echo "• Act as an OAuth-compatible gateway"
echo "• Handle authentication with a master key"
echo "• Forward requests to Anthropic Claude"
echo "• Provide usage tracking and logging"
echo ""
echo "Dashboard will be at: http://localhost:4000/ui"