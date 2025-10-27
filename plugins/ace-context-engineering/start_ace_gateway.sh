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
