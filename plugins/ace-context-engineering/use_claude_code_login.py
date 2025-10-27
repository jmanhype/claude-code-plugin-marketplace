#!/usr/bin/env python3
"""
Use existing OAuth token or claude-code-login tool to configure ACE
"""

import json
import os
import subprocess
from pathlib import Path

config_dir = Path.home() / ".config"

# Check for existing credentials
existing_token = config_dir / "ace_claude_max_token.json"
existing_api_key = config_dir / "ace_claude_max_api_key.txt"
claude_code_creds = Path.home() / "claude-code-login" / "credentials.json"

print("=" * 80)
print("Claude Code Setup for ACE")
print("=" * 80)
print()

# Option 1: Use existing OAuth credentials
if existing_token.exists() and existing_api_key.exists():
    print("✓ Found existing OAuth credentials from manual setup")
    print(f"  Token: {existing_token}")
    print(f"  API Key: {existing_api_key}")
    print()

    # Default to using existing credentials
    if True:
        api_key = existing_api_key.read_text().strip()
        print(f"Using API key: {api_key[:30]}...")

        # Create config
        config_file = config_dir / "ace_claude_code.env"
        config_file.write_text(f"""# Claude Code OAuth Configuration
# Generated from existing credentials

export ANTHROPIC_API_KEY="{api_key}"
export ACE_OAUTH_MODEL="claude-3-5-sonnet-20241022"
export ACE_OAUTH_VERSION="2023-06-01"
export ACE_OAUTH_BASE_URL="https://api.anthropic.com"
""")

        print()
        print("✅ Configuration saved!")
        print(f"   {config_file}")
        print()
        print("To use:")
        print(f"  source {config_file}")
        exit(0)

# Option 2: Use claude-code-login tool
if claude_code_creds.exists():
    print("✓ Found claude-code-login credentials")
    print(f"  {claude_code_creds}")
    print()

    # Read credentials
    creds = json.loads(claude_code_creds.read_text())
    access_token = creds['claudeAiOauth']['accessToken']

    print("Creating API key from OAuth token...")

    # Create API key
    import requests
    response = requests.post(
        "https://api.anthropic.com/api/oauth/claude_cli/create_api_key",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        timeout=30
    )

    if response.status_code == 200:
        api_key = response.json().get('raw_key')
        if api_key:
            print(f"✅ API key created: {api_key[:30]}...")

            # Save
            (config_dir / "ace_claude_max_api_key.txt").write_text(api_key)
            (config_dir / "claude_code_credentials.json").write_text(
                claude_code_creds.read_text()
            )

            # Create config
            config_file = config_dir / "ace_claude_code.env"
            config_file.write_text(f"""# Claude Code OAuth Configuration
# Generated from claude-code-login

export ANTHROPIC_API_KEY="{api_key}"
export ACE_OAUTH_MODEL="claude-3-5-sonnet-20241022"
export ACE_OAUTH_VERSION="2023-06-01"
export ACE_OAUTH_BASE_URL="https://api.anthropic.com"
""")

            print()
            print("✅ Configuration saved!")
            print(f"   {config_file}")
            print()
            print("To use:")
            print(f"  source {config_file}")
            exit(0)

    print(f"❌ Failed to create API key: {response.status_code}")
    print(response.text[:500])

# Option 3: Run claude-code-login setup
print()
print("No existing credentials found.")
print()
print("Run the setup script to configure Claude Code OAuth:")
print("  ./setup_claude_code_with_login.sh")
print()
print("Or use the claude-code-login tool directly:")
print("  cd ~/claude-code-login")
print("  bun run index.ts")
