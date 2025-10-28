# ACE: 100% GitHub Action (No API Keys!)

Run ACE benchmarks using **only** GitHub Actions with OAuth - zero API keys, zero local setup.

## 🎯 The Right Way

We use `claude-code-action` which handles OAuth automatically. No API keys needed!

```yaml
- uses: grll/claude-code-action@beta
  with:
    use_oauth: true
    claude_access_token: ${{ secrets.CLAUDE_ACCESS_TOKEN }}
    claude_refresh_token: ${{ secrets.CLAUDE_REFRESH_TOKEN }}
    claude_expires_at: ${{ secrets.CLAUDE_EXPIRES_AT }}
    secrets_admin_pat: ${{ secrets.SECRETS_ADMIN_PAT }}

    direct_prompt: |
      Run ACE benchmarks on AppWorld tasks...
```

## ✅ Benefits

1. **No API Keys** - Uses OAuth from claude-code-action
2. **Auto Token Refresh** - `secrets_admin_pat` handles expiration
3. **Claude Max Subscription** - Use your existing subscription
4. **One Setup** - Configure OAuth once, works forever
5. **Production Ready** - Battle-tested by claude-code-action users

## 🚀 Setup (5 Minutes)

### Step 1: Get OAuth Credentials

Follow the installer from claude-code-action:

```bash
# cd into your repo
bash <(curl -fsSL https://raw.githubusercontent.com/grll/claude-code-action/main/scripts/installer.sh)
```

This will:
1. Guide you through OAuth flow
2. Create the required secrets in your repo:
   - `CLAUDE_ACCESS_TOKEN`
   - `CLAUDE_REFRESH_TOKEN`
   - `CLAUDE_EXPIRES_AT`
3. Ask you to create `SECRETS_ADMIN_PAT` for auto-refresh

### Step 2: Create SECRETS_ADMIN_PAT

This token allows auto-refresh of OAuth tokens:

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: "Claude Code Secrets Admin"
4. Select scopes:
   - ✅ `repo` (full control)
   - ✅ No other scopes needed
5. Click "Generate token"
6. Copy the token (starts with `ghp_`)
7. Go to your repo secrets: https://github.com/jmanhype/claude-code-plugin-marketplace/settings/secrets/actions
8. Add secret:
   - Name: `SECRETS_ADMIN_PAT`
   - Value: `ghp_...` (the token you copied)

### Step 3: Install Claude GitHub App

```bash
# Visit and install:
https://github.com/apps/claude

# Select repository:
jmanhype/claude-code-plugin-marketplace
```

### Step 4: Run Workflow

```bash
gh workflow run ace-benchmark-v2.yml \
  -f num_tasks=3 \
  -f split=dev
```

Done! No API keys, no OAuth complexity on your end.

## 🏗️ How It Works

### Architecture

```
GitHub Actions Workflow
  ↓
claude-code-action (handles OAuth)
  ↓
Claude Code (with full context)
  ↓
Executes ACE benchmark code
  ↓
Results committed to git
```

### OAuth Flow (Automatic)

```
1. Workflow starts
2. claude-code-action loads OAuth tokens from secrets
3. If expired, uses SECRETS_ADMIN_PAT to refresh
4. Updates secrets automatically
5. Invokes Claude Code with valid token
6. Claude executes ACE benchmarks
7. Results saved to git
```

### No API Keys Anywhere!

❌ **Old approach** (WRONG):
```yaml
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}  # DON'T DO THIS
```

✅ **New approach** (CORRECT):
```yaml
uses: grll/claude-code-action@beta
with:
  use_oauth: true  # Uses OAuth, not API key!
  claude_access_token: ${{ secrets.CLAUDE_ACCESS_TOKEN }}
  claude_refresh_token: ${{ secrets.CLAUDE_REFRESH_TOKEN }}
  ...
```

## 📋 Workflow Configuration

### Direct Prompt Approach

The workflow uses `direct_prompt` to tell Claude what to do:

```yaml
direct_prompt: |
  You are running ACE benchmarks on AppWorld tasks.

  CONTEXT:
  - AppWorld is at /tmp/appworld
  - Playbook is at plugins/ace-context-engineering/skills/playbook.json
  - Task list is at plugins/ace-context-engineering/tasks_to_run.json

  YOUR JOB:
  1. Read task list
  2. For each task:
     - Load playbook bullets
     - Generate code with ACE generator
     - Execute in AppWorld
     - Record results
  3. Save results to JSON
  4. Update playbook with learnings

  Run the benchmarks now.
```

Claude Code receives this prompt and executes the entire benchmark autonomously.

### Allowed Tools

```yaml
allowed_tools: |
  Bash      # Run AppWorld execution
  Edit      # Update playbook
  Read      # Load tasks and playbook
  Write     # Save results
```

## 🔄 Automatic Token Refresh

The `secrets_admin_pat` enables automatic token refresh:

1. **OAuth tokens expire after 8 hours**
2. **claude-code-action detects expiration**
3. **Uses SECRETS_ADMIN_PAT to refresh**
4. **Updates GitHub secrets automatically**
5. **Workflow continues without interruption**

This means you set it up once and never think about it again!

## 📊 What Gets Created

### Files Per Run

```
plugins/ace-context-engineering/results/
├── run-1.json      # Detailed results
├── run-1.md        # Markdown report
├── run-2.json
├── run-2.md
└── ...
```

### Playbook Updates

```
plugins/ace-context-engineering/skills/
└── playbook.json   # Auto-updated with learnings
```

### Git Commits

```
commit abc123
chore: ACE benchmark results run #1

- Tasks: 3
- Split: dev
- Workflow: 123456789

🤖 Generated with [Claude Code]
```

## 🆚 Comparison

| Aspect | API Key Approach ❌ | OAuth Action ✅ |
|--------|---------------------|-----------------|
| **Setup** | Create API key manually | One-time OAuth flow |
| **Tokens** | Never expire (security risk) | Auto-refresh every 8hrs |
| **Cost** | Pay-per-token | Use Claude Max subscription |
| **Security** | API key in secrets | OAuth with auto-refresh |
| **Maintenance** | Manual if key rotates | Zero - fully automatic |
| **Integration** | Custom code needed | Built into action |

## 🎬 Usage Examples

### Quick Test (3 Tasks)

```bash
gh workflow run ace-benchmark-v2.yml \
  -f num_tasks=3 \
  -f split=dev
```

### Full Benchmark (10 Tasks)

```bash
gh workflow run ace-benchmark-v2.yml \
  -f num_tasks=10 \
  -f split=train
```

### Watch Progress

```bash
gh run watch
```

### View Results

```bash
# Latest results
cat plugins/ace-context-engineering/results/run-*.json | tail -1 | jq .

# Markdown report
cat plugins/ace-context-engineering/results/run-*.md | tail -1
```

## 🔐 Security

### OAuth Tokens (Encrypted)

- ✅ Stored encrypted in GitHub Secrets
- ✅ Auto-refresh prevents expiration
- ✅ Never exposed in logs
- ✅ Scoped to your account only

### SECRETS_ADMIN_PAT

- ✅ Only has `repo` scope
- ✅ Used only for refreshing secrets
- ✅ Can be revoked anytime
- ✅ Encrypted in GitHub Secrets

### No API Keys

- ✅ Zero API keys = zero key leakage risk
- ✅ No manual rotation needed
- ✅ No accidental commits
- ✅ Uses same auth as claude-code-action

## 💰 Cost

### GitHub Actions
- **Free** for public repos
- **Unlimited** minutes

### Claude Max Subscription
- **Included** in your existing subscription
- **No additional** API costs
- **Same quota** as interactive use

## 🐛 Troubleshooting

### "OAuth token expired"

**Fix**: Make sure `SECRETS_ADMIN_PAT` is set correctly. It should auto-refresh.

### "SECRETS_ADMIN_PAT not found"

**Fix**: Create PAT with `repo` scope and add to repository secrets.

### "Claude GitHub App not installed"

**Fix**: Install at https://github.com/apps/claude

### Workflow doesn't start

**Check**:
1. Are all OAuth secrets set?
2. Is `SECRETS_ADMIN_PAT` set?
3. Is Claude GitHub App installed?
4. Do you have permission to run workflows?

## 📚 Related Docs

- **claude-code-action**: https://github.com/grll/claude-code-action
- **OAuth Setup Guide**: Their installer handles everything
- **ACE Architecture**: `ACE_CICD_ARCHITECTURE.md`

## ✅ Migration Checklist

- [ ] Run claude-code-action installer script
- [ ] OAuth secrets created (ACCESS_TOKEN, REFRESH_TOKEN, EXPIRES_AT)
- [ ] SECRETS_ADMIN_PAT created and added
- [ ] Claude GitHub App installed
- [ ] Test workflow run completed
- [ ] Results committed to git
- [ ] **Remove any ANTHROPIC_API_KEY secrets** (not needed!)

## 🎯 Summary

**The Right Way to Run ACE in CI/CD**:

1. Use `claude-code-action` (handles OAuth)
2. Set up OAuth once with installer
3. Create `SECRETS_ADMIN_PAT` for auto-refresh
4. Use `direct_prompt` to invoke Claude
5. No API keys, no manual token management
6. Fully automatic, production-ready

---

**Status**: OAuth-only approach
**API Keys Needed**: ZERO
**Manual Steps After Setup**: ZERO
**It Just Works**: ✅

🤖 Generated with [Claude Code](https://claude.com/claude-code)
