# Automagik Forge Automation Analysis

Deep research into how https://github.com/namastexlabs/automagik-forge implements automated releases with the `automagik-genie` bot.

## 🔍 Key Discovery

**They're NOT using Claude Max OAuth or any AI for commits!**

The `automagik-genie` bot is a **simple GitHub Actions automation** that:
- Uses standard `GITHUB_TOKEN` (not API keys, not OAuth)
- Configures git user as "Automagik Genie"
- Creates version bump commits automatically
- No AI involvement in the automation

## How It Works

### 1. GitHub Actions Workflow

**File:** `.github/workflows/release.yml`

```yaml
name: 🚀 Unified Release

on:
  push:
    branches:
      - main
  pull_request:
    types: [closed]
    branches:
      - main
  workflow_dispatch:
    inputs:
      action:
        type: choice
        options:
          - 'bump-rc'
          - 'promote-to-stable'
          - 'manual-tag'

permissions:
  contents: write
  pull-requests: write
  packages: write
  actions: write

jobs:
  release:
    runs-on: ubuntu-22.04
    steps:
      - name: 📥 Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}
          submodules: recursive

      - name: 🔧 Configure Git
        run: |
          git config --global user.email "genie@namastex.ai"
          git config --global user.name "Automagik Genie"

      # ... more steps to bump version, commit, push
```

### 2. The "Bot" is Just Git Config

**What creates the "automagik-genie" bot:**

```bash
git config --global user.name "Automagik Genie"
git config --global user.email "genie@namastex.ai"
```

That's it! When the GitHub Action runs and creates commits, they appear as coming from "Automagik Genie" because that's the configured git user.

### 3. Authentication

**Uses standard GitHub Actions token:**
```yaml
with:
  token: ${{ secrets.GITHUB_TOKEN }}
```

- ✅ No API keys needed
- ✅ No OAuth setup needed
- ✅ No external services needed
- ✅ Built into GitHub Actions

The `GITHUB_TOKEN` is automatically provided by GitHub Actions and has permission to push back to the repository.

### 4. Commit Creation

**Latest commit by automagik-genie:**
```
SHA: 0d3de569a79f58ff9dc7e56c9e79d2a0d7565ee3
Author: Automagik Genie <genie@namastex.ai>
Committer: Automagik Genie <genie@namastex.ai>
Message: "chore: pre-release v0.4.7-rc.8"
Date: 2025-10-27T21:52:06Z
Verified: false (unsigned)
```

**Key observations:**
- Standard git commit (not signed)
- Created by GitHub Actions runner
- Uses configured git user name/email
- No special authentication required

### 5. The Automation Flow

```
Human pushes code to main
    ↓
GitHub Actions triggers release.yml
    ↓
Workflow checks out code with GITHUB_TOKEN
    ↓
Configures git user as "Automagik Genie"
    ↓
Runs version bump script (updates package.json)
    ↓
Creates commit with new version
    ↓
Pushes back to main using GITHUB_TOKEN
    ↓
Commit appears on GitHub from "automagik-genie"
```

## What This Means for ACE

### ✅ We CAN Do This for ACE!

We can create an "ACE Bot" the same way:

```yaml
name: ACE Benchmark Bot

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:
    inputs:
      num_tasks:
        type: string
        default: '3'

permissions:
  contents: write

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Configure Git
        run: |
          git config --global user.name "ACE Bot"
          git config --global user.email "ace-bot@claude-code-marketplace"

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Dependencies
        run: |
          pip install anthropic requests scikit-learn numpy

      - name: Run ACE Benchmarks
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          cd plugins/ace-context-engineering
          python benchmarks/run_appworld_standalone.py \
            --split dev \
            --max-samples ${{ inputs.num_tasks || '3' }} \
            --output results/run-${{ github.run_number }}.json

      - name: Commit Results
        run: |
          git add plugins/ace-context-engineering/results/
          git add plugins/ace-context-engineering/skills/playbook.json
          git commit -m "chore: ACE benchmark results run #${{ github.run_number }}" || true
          git push
```

### ❌ But There's Still One Problem

**We still need `ANTHROPIC_API_KEY` for the actual ACE code generation.**

The automagik-forge automation doesn't solve our OAuth problem because:
- They're not using AI in their automation
- They're just bumping version numbers (no API calls)
- ACE needs to call Anthropic API to generate code
- **We're back to needing an API key**

## Comparison: Their Bot vs ACE Bot

| Aspect | Automagik Genie | ACE Bot (what we need) |
|--------|-----------------|------------------------|
| **Purpose** | Version bumps, releases | AI code generation benchmarks |
| **Git commits** | ✅ Simple (using GITHUB_TOKEN) | ✅ Simple (using GITHUB_TOKEN) |
| **External API calls** | ❌ None needed | ✅ **Required** (Anthropic API) |
| **Authentication** | Just GITHUB_TOKEN | GITHUB_TOKEN + API key |
| **Cost** | Free | Pay-per-token |
| **Automation** | ✅ Fully automated | ✅ Could be fully automated (with API key) |

## The Reality Check

### What We Learned

1. **Creating a "bot" user in commits is trivial:**
   ```bash
   git config user.name "ACE Bot"
   git config user.email "ace-bot@example.com"
   ```

2. **Pushing back to GitHub is built-in:**
   ```yaml
   - uses: actions/checkout@v4
     with:
       token: ${{ secrets.GITHUB_TOKEN }}
   ```

3. **Scheduled automation works fine:**
   ```yaml
   on:
     schedule:
       - cron: '0 2 * * *'
   ```

### What We Still Can't Do

**Use Claude Max subscription for automated API calls.**

The automagik-forge example shows us how to:
- ✅ Create automated commits from a bot
- ✅ Use GitHub Actions for scheduled workflows
- ✅ Push results back to the repo

But it doesn't help with:
- ❌ Making AI API calls without an API key
- ❌ Using Claude Max compute in automation
- ❌ OAuth for programmatic access

## Bottom Line

**The automagik-forge automation is great for non-AI tasks but doesn't solve our AI API authentication problem.**

We could implement the exact same bot pattern for ACE, but we'd still need:
- `ANTHROPIC_API_KEY` in secrets
- Billing enabled on Anthropic account
- Pay-per-token for all API calls

The "bot" appearance is just a git configuration trick - it has nothing to do with API authentication.

## Recommendation

**Option 1: Implement ACE Bot with API Key (WORKS)**
```bash
# Human adds billing to console.anthropic.com
# Generate API key
# Add to GitHub secrets as ANTHROPIC_API_KEY
# Use exact same pattern as automagik-forge
```

**Option 2: Keep Waiting for OAuth (BLOCKED)**
```
# Wait for Anthropic to support OAuth in API
# Could be weeks/months/never
# No timeline available
```

**Option 3: Hybrid Approach**
```
# Use API key for automated benchmarks (pay-per-token)
# Use Claude Max for manual testing (included)
# Accept the cost for automation
```

## Files to Study

If you want to implement the same pattern:

1. **Workflow:** https://github.com/namastexlabs/automagik-forge/blob/main/.github/workflows/release.yml
2. **Script:** https://github.com/namastexlabs/automagik-forge/blob/main/scripts/unified-release.cjs
3. **Package.json:** https://github.com/namastexlabs/automagik-forge/blob/main/package.json (see bump scripts)

## What Automagik Forge Actually Does

**Project Description:** "The Vibe Coding++™ platform - orchestrate multiple AI agents, experiment with isolated attempts, ship code you understand."

**Their use case:**
- Platform for orchestrating AI coding agents
- Supports Claude, Gemini, Cursor, etc.
- Uses git worktrees for isolated attempts
- Releases are version bumps (no AI in the automation)

**Key insight:** They use AI agents interactively (like Claude Max), then automate the boring stuff (releases, builds, tests) with GitHub Actions.

## The Irony

They built a platform for **orchestrating AI agents** but don't use AI agents to automate their own releases!

Instead, they use simple GitHub Actions with standard git operations - which is exactly what we can do for ACE bot commits... except we still need an API key for the actual AI code generation.

---

**TL;DR:** automagik-genie is just `git config user.name "Bot Name"` + GitHub Actions `GITHUB_TOKEN`. Doesn't solve OAuth problem for AI API calls. Still need API key for ACE.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
