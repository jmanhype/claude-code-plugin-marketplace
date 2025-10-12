# Quick Start Guide

Get up and running with Multi-Agent Intelligence Marketplace in 5 minutes.

## Step 1: Add Marketplace

```bash
/plugin marketplace add jmanhype/claude-code-plugins
```

## Step 2: Browse Plugins

```bash
/plugin
```

You'll see 19 available plugins organized by category.

## Step 3: Install Your First Plugin

### For Traders
```bash
/plugin install quant-trading-system
```

### For Developers
```bash
/plugin install core-dev-suite
```

### For GitHub Users
```bash
/plugin install github-automation-suite
```

## Step 4: Configure (if needed)

Some plugins need configuration. Check the plugin's README:

```bash
/plugin info quant-trading-system
```

Example configuration:
```bash
export EXCHANGE_API_KEY=your_key
export EXCHANGE_SECRET=your_secret
export PAPER_TRADING=true
```

## Step 5: Start Using

Plugins add:
- **Agents** - Specialized AI assistants
- **Commands** - Slash commands like `/crypto-trader`
- **Workflows** - Pre-built automation patterns
- **Hooks** - Automatic execution triggers

Example usage:
```bash
# Use an agent
Task with swarm-coordination agent: "Coordinate 5 agents to analyze this codebase"

# Run a command
/crypto-trader start

# Execute a workflow
Follow the crypto-trader.md workflow for automated trading
```

## Common Use Cases

### 1. Automated Trading
```bash
/plugin install quant-trading-system
/plugin install research-execution-pipeline
/plugin install market-intelligence

# Configure
export EXCHANGE_API_KEY=xxx
export EXCHANGE_SECRET=yyy
export PAPER_TRADING=true

# Start paper trading
/crypto-trader start
```

### 2. GitHub Automation
```bash
/plugin install github-automation-suite
/plugin install repo-management-tools

# Configure
export GITHUB_TOKEN=ghp_xxxxx

# Use PR manager
Task with pr-manager: "Review all open PRs and create summary"
```

### 3. Multi-Agent Research
```bash
/plugin install research-execution-pipeline
/plugin install swarm-coordination
/plugin install hive-mind-orchestration

# Start research loop
/research-loop start

# Results in logs/runs.jsonl
```

### 4. Full Development Suite
```bash
/plugin install core-dev-suite
/plugin install testing-qa-framework
/plugin install cicd-automation

# Development workflow
Task with planner: "Plan implementation of user authentication"
Task with coder: "Implement the authentication system"
Task with tester: "Create comprehensive test suite"
Task with reviewer: "Review code quality and security"
```

## Pro Tips

### 1. Install Multiple Plugins at Once
```bash
/plugin install quant-trading-system research-execution-pipeline market-intelligence
```

### 2. Check What's Installed
```bash
/plugin list
```

### 3. Update Plugins
```bash
/plugin update
```

### 4. Remove Unused Plugins
```bash
/plugin uninstall plugin-name
```

### 5. Get Help
```bash
/plugin help
/plugin info <plugin-name>
```

## Next Steps

1. **Explore Categories** - Browse plugins by category in the marketplace
2. **Read Plugin READMEs** - Each plugin has detailed documentation
3. **Join Community** - Share your use cases and get help
4. **Contribute** - Build and share your own plugins

## Troubleshooting

### Marketplace Not Found
```bash
# Make sure you added the marketplace
/plugin marketplace list

# Add if missing
/plugin marketplace add jmanhype/claude-code-plugins
```

### Plugin Installation Failed
```bash
# Check plugin name
/plugin search <partial-name>

# Try again with exact name
/plugin install exact-plugin-name
```

### Configuration Issues
```bash
# Check plugin requirements
/plugin info plugin-name

# Set required environment variables
export VAR_NAME=value

# Restart Claude Code
```

### Need Help?
- **Issues**: [GitHub Issues](https://github.com/jmanhype/claude-code-plugins/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jmanhype/claude-code-plugins/discussions)
- **Docs**: [Full Documentation](https://github.com/jmanhype/claude-code-plugins)

## What's Next?

Check out:
- [Use Case Guide](use-cases.md) - Detailed scenarios
- [Plugin Catalog](../README.md#all-plugins) - Complete plugin list
- [Advanced Configuration](advanced-config.md) - Power user features
- [Contributing Guide](../CONTRIBUTING.md) - Build your own plugins

---

**Happy coding with Multi-Agent Intelligence! 🧊💎**
