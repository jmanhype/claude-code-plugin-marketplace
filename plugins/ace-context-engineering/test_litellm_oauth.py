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
