# Automagik's Claude Code Usage - Investigation Results

## Investigation Summary

**Key Finding:** Automagik Forge **lists Claude Code as a supported agent** but does NOT use it for automated commits or CI/CD. The `automagik-genie` bot is pure GitHub Actions automation, not AI-assisted.

## What We Found

### 1. Claude Code in Their README

**From README.md:**
```markdown
Supported AI Coding Agents:
- Claude Code
- Cursor CLI
- Gemini
- Codex
- OpenCode
- Qwen Code
```

**What this means:**
- ✅ Users can choose Claude Code as an **agent** for manual tasks
- ✅ It's one of many AI tools their **platform supports**
- ❌ They don't use Claude Code for **automated** CI/CD
- ❌ No evidence of @claude automation in their workflows

### 2. How Users Actually Use Claude Code

**From their platform:**
```typescript
// User workflow:
1. User creates a task in Automagik Forge
2. User selects "Claude Code" as the agent
3. Automagik sends task to Claude Code (interactive)
4. User reviews the result
5. User decides to merge or try another agent
```

**This is interactive, not automated!**

### 3. What `automagik-genie` Actually Is

**Confirmed from investigation:**

| Aspect | Reality |
|--------|---------|
| **Bot commits** | Yes (version bumps) |
| **Uses AI** | ❌ No |
| **Uses Claude Code** | ❌ No |
| **Uses OAuth** | Only for their MCP server |
| **Automation** | GitHub Actions + git config |
| **Purpose** | Release management |

**The "bot" is literally just:**
```yaml
- name: Configure Git
  run: |
    git config --global user.name "Automagik Genie"
    git config --global user.email "genie@namastex.ai"
```

### 4. No Claude Code in CI/CD

**Searched for:**
- ❌ "claude code" in repository → 0 results
- ❌ "@claude" mentions → 0 results
- ❌ "Co-Authored-By: Claude" in commits → 0 results
- ❌ claude-code-action in workflows → 0 results
- ❌ ANTHROPIC_API_KEY in workflows → 0 results
- ❌ Pull requests by automagik-genie → 0 results

**Their CI/CD workflow (`.github/workflows/test.yml`):**
```yaml
# Standard testing only
- Checkout
- Setup Node.js
- npm install
- Lint and format
- Type checking
- Run tests
# No AI, no Claude Code, no API calls
```

### 5. Their OAuth Is Still Just MCP Server Auth

**What we confirmed:**
- They built an OAuth 2.1 **server** for their MCP tools
- Claude **Desktop** (not Claude Code Action) authenticates to it
- This is for **interactive** use, not CI/CD automation
- Still has nothing to do with Anthropic API authentication

## The Platform vs The Automation

### Their Platform (Interactive)

```
┌──────────────┐
│   Human      │ Creates task
└──────┬───────┘
       ↓
┌──────────────────────┐
│ Automagik Forge      │ Orchestration platform
│                      │
│ Choose agent:        │
│  • Claude Code   ←──── User can select this
│  • Cursor CLI        │
│  • Gemini            │
│  • etc.              │
└──────────────────────┘
       ↓
User reviews & decides
```

**Claude Code here is:**
- ✅ A choice for users
- ✅ Runs interactively
- ✅ User-controlled
- ❌ Not automated
- ❌ Not in CI/CD

### Their Automation (Non-AI)

```
Code pushed to main
    ↓
GitHub Actions triggers
    ↓
release.yml workflow runs
    ↓
Git config: "Automagik Genie"
    ↓
Bump version in package.json
    ↓
Commit + Push (appears from "bot")
    ↓
Done (no AI involved)
```

**The automation:**
- ✅ Pure GitHub Actions
- ✅ Simple git operations
- ❌ No AI
- ❌ No Claude Code
- ❌ No API calls

## Why This Doesn't Help ACE

### What We Hoped
"Maybe they use Claude Code in GitHub Actions with OAuth!"

### Reality
```
┌─────────────────────────────────────────┐
│ Automagik Forge Platform                │
│                                         │
│ Users:                                  │
│ • Can choose Claude Code interactively  │
│ • Run in git worktrees                  │
│ • Review and merge manually             │
│                                         │
│ Automation:                             │
│ • Just version bumps                    │
│ • No AI involved                        │
│ • No Claude Code                        │
│ • No API keys needed                    │
└─────────────────────────────────────────┘
```

### What ACE Needs

```
┌─────────────────────────────────────────┐
│ ACE Benchmarks (Automated)              │
│                                         │
│ Need:                                   │
│ • Automated code generation             │
│ • No human interaction                  │
│ • Call Anthropic API programmatically   │
│ • Run on schedule                       │
│                                         │
│ Blocked by:                             │
│ • Anthropic API doesn't accept OAuth    │
│ • Need API key with billing             │
│ • Can't use Claude Max for automation   │
└─────────────────────────────────────────┘
```

## Lessons from Automagik

### What They Do Well

1. **Support many AI agents** (including Claude Code)
   - Users choose interactively
   - Platform agnostic

2. **Simple automation for non-AI tasks**
   - Version bumps via GitHub Actions
   - No complexity, no API keys needed

3. **OAuth for MCP security**
   - Protect their own services
   - Standard implementation

### What They DON'T Do

1. ❌ Use AI in automated workflows
2. ❌ Use Claude Code in CI/CD
3. ❌ Solve OAuth for Anthropic API
4. ❌ Run code generation in GitHub Actions

## Final Verdict

**Automagik Forge is a platform where users can manually choose Claude Code as an agent, but their automated "genie" bot has nothing to do with AI or Claude Code.**

### Summary Table

| Feature | Automagik Has | ACE Needs |
|---------|--------------|-----------|
| Interactive Claude Code | ✅ Yes | ❌ No (we need automation) |
| Automated AI in CI/CD | ❌ No | ✅ Yes |
| OAuth for MCP | ✅ Yes (their server) | ❌ No (need API auth) |
| GitHub Actions bot | ✅ Yes (no AI) | ✅ Yes (with AI) |
| Anthropic API calls | ❌ No | ✅ Yes |
| API key needed | ❌ No | ✅ Yes |

## The Unchanged Reality

After investigating Automagik Forge thoroughly:

**For ACE automation in GitHub Actions, we still need:**
1. ❌ Anthropic API key
2. ❌ Billing enabled
3. ❌ Pay per token
4. ❌ Can't use Claude Max OAuth

**Automagik doesn't change this because:**
- They support Claude Code **interactively** (user-driven)
- Their automation is **non-AI** (just version bumps)
- Their OAuth is **for their server** (not Anthropic API)

## Conclusion

**Automagik Forge lists Claude Code as a supported agent for interactive use, but does not use it (or any AI) in their automated CI/CD workflows.**

The `automagik-genie` bot is a simple GitHub Actions automation using git config tricks, not an AI-powered assistant. Their OAuth implementation protects their own MCP server, not Anthropic's API.

**Nothing about their setup helps us use Claude Max OAuth for automated ACE benchmarks.**

---

**Current status:** Still need API key for ACE automation. No workarounds discovered.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
