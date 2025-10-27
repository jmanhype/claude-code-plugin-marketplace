# Claude Code Login Integration 🚀

This guide shows how to use the excellent [claude-code-login](https://github.com/grll/claude-code-login) tool with the ACE context engineering plugin.

## Why claude-code-login?

The `claude-code-login` tool by @grll is a clean, well-maintained TypeScript solution for Claude Code OAuth authentication:

- ✅ **Simple**: Just 2 commands to get OAuth tokens
- ✅ **Secure**: Uses OAuth 2.0 with PKCE
- ✅ **Well-tested**: Comprehensive test suite
- ✅ **GitHub Actions ready**: Built-in CI/CD support
- ✅ **Actively maintained**: Up-to-date with latest Claude API

## Quick Start

### Option 1: Use Your Existing Credentials ✅

If you've already completed the manual OAuth setup, you're done!

```bash
# Configure ACE to use your existing credentials
cd /Users/speed/claude-code-plugin-marketplace/plugins/ace-context-engineering
python3 ./use_claude_code_login.py

# Load the configuration
source ~/.config/ace_claude_code.env
```

**That's it!** Your ACE plugin is now configured to use Claude Code.

### Option 2: Fresh Setup with claude-code-login

If you want to start fresh or prefer the claude-code-login tool:

```bash
# 1. Clone and setup
cd ~
git clone https://github.com/grll/claude-code-login.git
cd claude-code-login
bun install

# 2. Generate login URL
bun run index.ts

# 3. Open the URL in your browser and authorize

# 4. Copy the authorization code from the callback URL
# It will look like: https://console.anthropic.com/oauth/code/callback?code=XXXXX

# 5. Exchange code for tokens
bun run index.ts <your_code_here>

# 6. Configure ACE
cd /Users/speed/claude-code-plugin-marketplace/plugins/ace-context-engineering
python3 ./use_claude_code_login.py
```

## What Gets Configured

The setup creates the following:

### 1. Environment Configuration
**Location**: `~/.config/ace_claude_code.env`

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
export ACE_OAUTH_MODEL="claude-3-5-sonnet-20241022"
export ACE_OAUTH_VERSION="2023-06-01"
export ACE_OAUTH_BASE_URL="https://api.anthropic.com"
```

### 2. Credentials Storage
- `~/.config/claude_code_credentials.json` - OAuth tokens (if using claude-code-login)
- `~/.config/ace_claude_max_api_key.txt` - API key for direct use
- `~/.config/ace_claude_max_token.json` - OAuth tokens (if using manual setup)

## Usage

### Load Configuration

```bash
# Temporary (current session only)
source ~/.config/ace_claude_code.env

# Permanent (add to shell profile)
echo 'source ~/.config/ace_claude_code.env' >> ~/.zshrc
```

### Verify Setup

```bash
cd /Users/speed/claude-code-plugin-marketplace/plugins/ace-context-engineering
python3 test_claude_code_oauth.py
```

Expected output:
```
✓ ANTHROPIC_API_KEY
✓ ACE_OAUTH_MODEL
...
API Key: sk-ant-api03-...
```

## How It Works

### Authentication Flow

```
1. Generate OAuth URL with PKCE
   ↓
2. User authorizes in browser
   ↓
3. Redirect with authorization code
   ↓
4. Exchange code for access token
   ↓
5. Create API key from OAuth token
   ↓
6. Configure ACE environment
```

### Key Components

1. **claude-code-login** (`~/claude-code-login/`)
   - Handles OAuth flow with PKCE
   - Manages state verification
   - Saves credentials to `credentials.json`

2. **Integration Scripts** (ACE plugin)
   - `use_claude_code_login.py` - Detects and configures credentials
   - `setup_claude_code_with_login.sh` - Full automated setup
   - `test_claude_code_oauth.py` - Verify configuration

3. **ACE Configuration** (`~/.config/`)
   - `ace_claude_code.env` - Environment variables
   - Credentials and tokens

## Advanced Usage

### Using with GitHub Actions

The claude-code-login tool supports GitHub Actions for CI/CD:

```yaml
name: Claude OAuth
on:
  workflow_dispatch:
    inputs:
      code:
        description: 'Authorization code'
        required: false

jobs:
  auth:
    runs-on: ubuntu-latest
    steps:
      - uses: grll/claude-code-login@v1
        with:
          code: ${{ inputs.code }}
          secrets_admin_pat: ${{ secrets.SECRETS_ADMIN_PAT }}
```

See the [claude-code-login README](https://github.com/grll/claude-code-login#github-actions) for details.

### Manual Token Refresh

OAuth tokens expire after 8 hours. To refresh:

```bash
# Option 1: Re-run claude-code-login
cd ~/claude-code-login
bun run index.ts  # Generate new URL
bun run index.ts <new_code>  # Exchange for tokens

# Option 2: Use existing refresh token
# (Implementation in claude-code-login handles this automatically)
```

### Multiple Accounts

To use different Claude accounts:

```bash
# Save credentials with different names
cp ~/.config/claude_code_credentials.json ~/.config/claude_code_work.json
cp ~/.config/claude_code_credentials.json ~/.config/claude_code_personal.json

# Switch between them
export CLAUDE_CODE_CREDENTIALS=~/.config/claude_code_work.json
source ~/.config/ace_claude_code.env
```

## Troubleshooting

### "Credit balance too low"

This is expected! The OAuth flow works perfectly. You just need to:
1. Go to https://console.anthropic.com/settings/billing
2. Add credits or configure billing

### "State has expired"

The OAuth state is only valid for 10 minutes. Simply:
1. Generate a new URL: `bun run index.ts`
2. Authorize and get new code
3. Exchange within 10 minutes

### "Could not load state data"

You need to run step 1 first:
```bash
cd ~/claude-code-login
bun run index.ts  # This creates the state file
# Then authorize and run step 2
```

## Comparison: Manual vs claude-code-login

| Feature | Manual Setup | claude-code-login |
|---------|--------------|-------------------|
| Complexity | High (custom scripts) | Low (2 commands) |
| Dependencies | Python, requests | Bun, TypeScript |
| GitHub Actions | Custom | Built-in |
| Maintenance | DIY | Community maintained |
| Testing | Manual | Automated test suite |
| **Recommendation** | For learning | **For production** |

## Files Reference

### ACE Plugin Files
```
plugins/ace-context-engineering/
├── use_claude_code_login.py          # Main integration script
├── setup_claude_code_with_login.sh   # Automated setup
├── test_claude_code_oauth.py         # Test configuration
├── CLAUDE_CODE_LOGIN_INTEGRATION.md  # This file
└── CLAUDE_CODE_OAUTH_SETUP.md       # Manual setup docs (legacy)
```

### Configuration Files
```
~/.config/
├── ace_claude_code.env              # Environment variables
├── claude_code_credentials.json      # OAuth tokens (claude-code-login)
├── ace_claude_max_token.json        # OAuth tokens (manual)
└── ace_claude_max_api_key.txt       # API key
```

### claude-code-login Files
```
~/claude-code-login/
├── index.ts                         # Main OAuth implementation
├── credentials.json                 # Generated tokens
└── claude_oauth_state.json         # Temporary state (auto-cleanup)
```

## Next Steps

1. ✅ OAuth configured
2. ⏳ Add billing/credits at console.anthropic.com
3. 🚀 Start using ACE with Claude Code!

Once billing is configured, you can:
- Run ACE benchmarks with your Claude Max subscription
- Use the full context engineering features
- Integrate with AppWorld and other frameworks

## Credits

- [claude-code-login](https://github.com/grll/claude-code-login) by @grll - Excellent OAuth tool
- ACE Context Engineering plugin - Uses the OAuth credentials

---

**Setup Status**: ✅ Complete
**Last Updated**: Mon Oct 27, 2025
