# Claude Code GitHub Action Setup

This repository now includes automated Claude Code assistance for Pull Requests and Issues using the [claude-code-action](https://github.com/grll/claude-code-action) by @grll.

## What It Does

Claude can now:
- 💬 **Answer questions** about code in PRs and issues
- 🔍 **Review pull requests** and suggest improvements
- ✨ **Implement code changes** when requested
- 🐛 **Fix bugs** from screenshots or descriptions
- 📝 **Update documentation** automatically

## Quick Start

### 1. Add the API Key Secret

The workflow file (`.github/workflows/claude.yml`) is already set up. You just need to add your Anthropic API key:

```bash
# You already have the API key at:
cat ~/.config/ace_claude_max_api_key.txt

# Add it to GitHub repository secrets:
# 1. Go to: https://github.com/jmanhype/claude-code-plugin-marketplace/settings/secrets/actions
# 2. Click "New repository secret"
# 3. Name: ANTHROPIC_API_KEY
# 4. Value: sk-ant-api03-4kTcRBd... (paste the full key)
# 5. Click "Add secret"
```

### 2. Install the Claude GitHub App

The action requires the Claude GitHub App for permissions:

```bash
# Visit and install:
https://github.com/apps/claude

# Select repository:
jmanhype/claude-code-plugin-marketplace
```

### 3. Test It

Create a test issue or PR comment:

```
@claude What does the ACE code generator do?
```

Claude will respond with an explanation!

## Usage Examples

### Ask Questions

In any PR or issue:
```
@claude How does the bullet retriever work?
```

### Request Code Changes

```
@claude Can you add error handling to the code generator?
```

### Get Code Reviews

```
@claude Please review this PR and suggest improvements
```

### Fix Bugs from Screenshots

Upload a screenshot and say:
```
@claude Here's a bug I'm seeing [screenshot]. Can you fix it?
```

## Configuration

The workflow is configured in `.github/workflows/claude.yml`:

### Current Settings

- **Trigger**: `@claude` in comments, PR reviews, or issue bodies
- **Timeout**: 60 minutes
- **Max Turns**: 10 conversation turns
- **Permissions**: Can read/write to repo, PRs, and issues

### Optional Customizations

You can uncomment and modify these in `claude.yml`:

```yaml
# Change trigger phrase
trigger_phrase: "/claude"

# Limit available tools
allowed_tools: |
  Bash(npm install)
  Bash(npm test)
  Edit

# Add custom instructions
custom_instructions: |
  Always run tests before making changes.
  Follow the project's coding style guide.
```

## How It Works

1. **Trigger Detection**: Action activates when `@claude` appears in:
   - Issue comments
   - PR comments
   - PR review comments
   - Issue/PR bodies

2. **Context Gathering**: Claude analyzes:
   - PR changes (if in a PR)
   - Issue description
   - All related comments
   - Repository code

3. **Smart Response**: Claude either:
   - Answers questions in a comment
   - Creates code changes on a new branch
   - Pushes changes directly to the PR branch

4. **Branch Management**:
   - **On issues**: Creates new branch `claude/issue-123`
   - **On open PRs**: Pushes directly to PR branch
   - **On closed PRs**: Creates new branch

## What Claude Can Do

✅ **Capabilities**:
- Analyze code and explain how it works
- Implement code changes (simple to moderate)
- Fix bugs and add error handling
- Write tests and documentation
- Review code and suggest improvements
- Create new features
- Refactor code

❌ **Limitations**:
- Cannot approve PRs (security)
- Cannot submit formal PR reviews
- Cannot merge branches
- Cannot access CI/CD results (unless configured)
- Limited to repository context

## Security

- ✅ Only users with **write access** can trigger the action
- ✅ Bots and GitHub Apps **cannot** trigger it
- ✅ API key stored securely in GitHub secrets
- ✅ Short-lived tokens scoped to single repository
- ✅ All commits are cryptographically signed
- ✅ No cross-repository access

## Cost Considerations

The action uses your Anthropic API credits. To manage costs:

1. **Limit max_turns** (currently 10):
   ```yaml
   max_turns: "5"  # Reduces conversation length
   ```

2. **Shorter timeout** (currently 60 min):
   ```yaml
   timeout_minutes: "30"
   ```

3. **Monitor usage** at: https://console.anthropic.com/settings/billing

## Troubleshooting

### "Credit balance too low"

You need to add billing at: https://console.anthropic.com/settings/billing

### Action doesn't trigger

Check:
1. Is the Claude GitHub App installed?
2. Is `ANTHROPIC_API_KEY` in repository secrets?
3. Did you use the correct trigger phrase (`@claude`)?
4. Do you have write access to the repository?

### Permission errors

The action needs these permissions (already configured):
```yaml
permissions:
  contents: write
  pull-requests: write
  issues: write
  id-token: write
```

## Advanced: Custom MCP Servers

You can extend Claude's capabilities with MCP (Model Context Protocol) servers:

```yaml
- uses: grll/claude-code-action@beta
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    mcp_config: |
      {
        "mcpServers": {
          "sequential-thinking": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
          }
        }
      }
    allowed_tools: "mcp__sequential-thinking__sequentialthinking"
```

See [MCP documentation](https://github.com/grll/claude-code-action#using-custom-mcp-configuration) for details.

## Comparison: Local ACE vs GitHub Action

| Feature | ACE OAuth Client | claude-code-action |
|---------|------------------|-------------------|
| **Purpose** | Local benchmarks | GitHub automation |
| **Trigger** | Manual Python scripts | `@claude` comments |
| **Auth** | API key | API key |
| **Token Refresh** | Manual | Automatic |
| **Use Case** | AppWorld benchmarks | PR/issue assistance |
| **Location** | Your machine | GitHub Actions |

Both tools complement each other:
- Use **ACE** for running benchmarks and local development
- Use **claude-code-action** for automated GitHub assistance

## Next Steps

1. ✅ Workflow file created (`.github/workflows/claude.yml`)
2. ⏳ Add `ANTHROPIC_API_KEY` to GitHub secrets
3. ⏳ Install Claude GitHub App
4. 🚀 Start using `@claude` in PRs and issues!

---

**Setup Status**: Workflow configured, secrets needed
**Documentation**: This file + [Full README](https://github.com/grll/claude-code-action)
**Last Updated**: Mon Oct 27, 2025
