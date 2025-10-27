# Claude Code Integration Comparison

## Overview

There are multiple ways to use Claude with OAuth authentication. This document compares the approaches and recommends when to use each.

## Three Integration Approaches

### 1. claude-code-login (Token Generator)
**Repository**: https://github.com/grll/claude-code-login
**Purpose**: Generate OAuth tokens for local use

**Pros**:
- ✅ Simple 2-step OAuth flow
- ✅ TypeScript/Bun based
- ✅ Saves tokens to `credentials.json`
- ✅ Good for one-time token generation

**Cons**:
- ❌ No automatic token refresh
- ❌ Tokens expire after 8 hours
- ❌ Manual re-authentication required
- ❌ Not suitable for long-running workflows

**Use When**:
- Generating initial OAuth tokens
- Quick local testing
- Learning OAuth flow

### 2. claude-code-action (GitHub Action)
**Repository**: https://github.com/grll/claude-code-action (OAuth fork)
**Purpose**: GitHub CI/CD automation with Claude

**Pros**:
- ✅ Full GitHub integration (PR reviews, issue responses)
- ✅ Automatic token refresh via `secrets_admin_pat`
- ✅ No manual token management
- ✅ Production-ready CI/CD
- ✅ One-command installer script
- ✅ Battle-tested in many repos

**Cons**:
- ❌ Only works in GitHub Actions
- ❌ Not for local development
- ❌ Requires GitHub app installation
- ❌ Designed for automation, not programmatic use

**Use When**:
- Automating PR reviews
- Bot responses to issues
- CI/CD workflows
- GitHub-centric automation

### 3. ACE OAuth Client (Our Implementation)
**File**: `anthropic_oauth_client.py`
**Purpose**: Programmatic Claude API access for ACE benchmarks

**Pros**:
- ✅ Direct Anthropic API integration
- ✅ Works locally and in CI
- ✅ Token caching to disk
- ✅ No GitHub dependency
- ✅ Full programmatic control
- ✅ Integrated with ACE skill system

**Cons**:
- ❌ Requires ngrok for OAuth callback
- ❌ Manual token refresh (expires after 8 hours)
- ❌ More complex setup
- ❌ Custom implementation

**Use When**:
- Running ACE benchmarks locally
- Programmatic skill invocation
- Local development/testing
- Non-GitHub workflows

## Recommended Architecture

### For GitHub Automation
Use **claude-code-action**:

```yaml
# .github/workflows/claude.yml
- uses: grll/claude-code-action@beta
  with:
    use_oauth: true
    claude_access_token: ${{ secrets.CLAUDE_ACCESS_TOKEN }}
    claude_refresh_token: ${{ secrets.CLAUDE_REFRESH_TOKEN }}
    claude_expires_at: ${{ secrets.CLAUDE_EXPIRES_AT }}
    secrets_admin_pat: ${{ secrets.SECRETS_ADMIN_PAT }}
```

**Benefits**:
- Auto-refreshes tokens
- No maintenance required
- Production-ready

### For Local Development/Benchmarks
Use **ACE OAuth Client** with tokens from claude-code-login:

```bash
# 1. Get initial tokens (one-time)
cd ~/claude-code-login
bun run index.ts  # Generate URL
bun run index.ts <code>  # Exchange for tokens

# 2. Configure ACE to use tokens
python use_claude_code_login.py

# 3. Run benchmarks
source ~/.config/ace_claude_code.env
python -m benchmarks.run_appworld
```

**Benefits**:
- Works without GitHub
- Full control over execution
- Integrated with ACE skills

## Migration Path

### Current State
We currently use:
- ❌ claude-code-login (tokens expire too quickly)
- ✅ ACE OAuth Client (good for local use)
- ❌ No GitHub automation

### Recommended State
Use **both** for different purposes:

1. **GitHub Automation** → claude-code-action
   - Install via one-command script
   - Handles PR reviews automatically
   - Auto-refreshes OAuth tokens

2. **Local Benchmarks** → ACE OAuth Client
   - Keep existing implementation
   - Use API key instead of OAuth tokens
   - More reliable for long-running benchmarks

## Implementation Plan

### Option A: Hybrid Approach (Recommended)

**For GitHub CI/CD:**
```bash
# Install claude-code-action for GitHub automation
bash <(curl -fsSL https://raw.githubusercontent.com/grll/claude-code-action/main/scripts/installer.sh)
```

**For Local Development:**
```bash
# Use API key instead of OAuth (more reliable)
export ANTHROPIC_API_KEY="sk-ant-api03-..."
source ~/.config/ace_claude_code.env
```

### Option B: API Key Only (Simplest)

**Abandon OAuth entirely, use direct API key:**

```bash
# Create API key at console.anthropic.com
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# Works everywhere:
# - Local development ✅
# - GitHub Actions ✅
# - CI/CD ✅
# - Long-running benchmarks ✅
```

**Benefits**:
- No token expiration issues
- No OAuth complexity
- Works identically everywhere
- No ngrok required

## Recommendation

**For ACE Plugin**: Use **Option B** (API Key Only)

**Reasoning**:
1. ACE benchmarks run for hours/days → OAuth tokens expire too quickly
2. API keys never expire → More reliable
3. Simpler setup → Less complexity
4. GitHub Actions support both → No loss of functionality
5. OAuth adds complexity without benefit for this use case

**For GitHub Automation**: Add **claude-code-action** separately

```yaml
# GitHub Action uses API key too (simpler)
- uses: grll/claude-code-action@beta
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Conclusion

| Use Case | Solution | Auth Method |
|----------|----------|-------------|
| GitHub PR reviews | claude-code-action | API Key |
| GitHub issue responses | claude-code-action | API Key |
| Local ACE benchmarks | ACE OAuth Client | API Key |
| CI/CD workflows | claude-code-action | API Key |
| Quick testing | ACE OAuth Client | API Key |

**Bottom Line**: OAuth adds complexity without benefit. Use API keys for everything.

---

**Current Status**: We have OAuth working but should migrate to API keys
**Next Step**: Simplify by using ANTHROPIC_API_KEY everywhere
