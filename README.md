# 🧊 Multi-Agent Intelligence Marketplace

> Production-grade multi-agent systems for Claude Code - trading, automation, swarm intelligence, and agentic development

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude-Code-blue)](https://docs.claude.com/en/docs/claude-code)
[![Plugins: 21](https://img.shields.io/badge/Plugins-21-green)](https://github.com/jmanhype/claude-code-plugins)

Transform Claude Code into a specialized multi-agent system. Install curated plugins for AI safety monitoring, quantitative trading, GitHub automation, distributed coordination, and systematic development workflows.

## 🚀 Quick Start

Install the marketplace:

```bash
/plugin marketplace add jmanhype/claude-code-plugins
```

Browse and install plugins:

```bash
/plugin
```

## 📦 Featured Plugins

### 🛡️ Code Safety Monitor

**Install:** `/plugin install code-safety-monitor`

DSPy-powered AI safety monitoring system:

- 90% backdoor detection rate with 1% false positives
- GEPA-optimized prompt engineering (35x more efficient than RL)
- Real-time scanning and circuit breakers
- Comparative training on attack vs honest code

**Use Cases:**

- AI control research and production deployments
- Detecting backdoors in untrusted LLM-generated code
- Privacy-conscious delegation validation
- Vulnerability detection in web applications
- Scalable code auditing (review only ~1% of code)

---

### 🔧 Modular Agentic Development

**Install:** `/plugin install modular-agentic-dev`

Session-based agentic development framework:

- Session isolation and state management
- Hot-swappable agent composition
- Incremental task orchestration
- Workflow checkpointing

**Use Cases:**

- Complex multi-phase projects
- Iterative development cycles
- State-aware agent coordination
- Progressive feature delivery

---

### 🎯 Quantitative Trading System

**Install:** `/plugin install quant-trading-system`

Complete trading stack with:

- Risk management & position sizing
- Circuit breakers & kill switches
- Pre/post trade hooks
- Real-time safety guards
- CCXT exchange integration

**Use Cases:**

- Automated crypto trading
- Risk-controlled execution
- Paper & live trading modes
- 5-minute trading loops

---

### 🔬 Research-Execution Pipeline

**Install:** `/plugin install research-execution-pipeline`

DSPy-powered research system:

- Automated strategy discovery
- GEPA optimization methodology
- Continuous backtesting
- Benchmark-gated promotion

**Use Cases:**

- Systematic strategy research
- Alpha generation
- Daily research loops (06:00)
- Strategy evolution

---

### 🐙 GitHub Automation Suite

**Install:** `/plugin install github-automation-suite`

13 specialized GitHub agents:

- PR management & reviews
- Issue tracking & triage
- Release orchestration
- Multi-repo coordination
- Project board sync

**Use Cases:**

- Automate PR workflows
- Code review swarms
- Release management
- Multi-repo projects

---

### 🐝 Swarm Coordination

**Install:** `/plugin install swarm-coordination`

Advanced swarm patterns:

- Adaptive topology switching
- Hierarchical coordination
- Mesh networks
- Self-organizing systems

**Use Cases:**

- Distributed agent systems
- Dynamic workload routing
- Fault-tolerant coordination
- Scalable multi-agent AI

---

## 📋 Complete Plugin Catalog

| Plugin                          | Category      | Description                                  |
| ------------------------------- | ------------- | -------------------------------------------- |
| `code-safety-monitor`         | Safety        | DSPy-powered backdoor detection (90% TPR)    |
| `modular-agentic-dev`         | Methodology   | Session-based agentic development framework  |
| `quant-trading-system`        | Trading       | Complete quantitative trading stack          |
| `research-execution-pipeline` | Research      | DSPy research + GEPA optimization            |
| `github-automation-suite`     | GitHub        | 13 GitHub automation agents                  |
| `swarm-coordination`          | Swarm         | Adaptive/hierarchical/mesh coordinators      |
| `consensus-protocols`         | Distributed   | Byzantine/Raft/CRDT/Gossip consensus         |
| `core-dev-suite`              | Development   | Planner, coder, reviewer, tester, researcher |
| `market-intelligence`         | Trading       | Market analysis & monitoring                 |
| `repo-management-tools`       | GitHub        | Multi-repo coordination                      |
| `hive-mind-orchestration`     | Swarm         | Distributed decision-making                  |
| `testing-qa-framework`        | Testing       | TDD + validation + test automation           |
| `api-docs-generator`          | Documentation | OpenAPI/Swagger generation                   |
| `cicd-automation`             | DevOps        | GitHub Actions + CI/CD                       |
| `mobile-automation`           | Mobile        | React Native + ClassDojo workflows           |
| `performance-optimization`    | Optimization  | Load balancing + benchmarks                  |
| `architecture-design`         | Architecture  | System design + patterns                     |
| `memory-coordination`         | Coordination  | Memory + task orchestration                  |
| `safety-compliance`           | Safety        | Circuit breakers + guards                    |
| `sparc-methodology`           | Methodology   | SPARC development framework                  |
| `base-template-generator`     | Templates     | Project scaffolding                          |

## 🎯 Use Case Guides

### For AI Safety Researchers

```bash
/plugin install code-safety-monitor
/plugin install safety-compliance
/plugin install testing-qa-framework
```

### For Quant Traders

```bash
/plugin install quant-trading-system
/plugin install research-execution-pipeline
/plugin install market-intelligence
```

### For GitHub Power Users

```bash
/plugin install github-automation-suite
/plugin install repo-management-tools
/plugin install cicd-automation
```

### For Distributed Systems Engineers

```bash
/plugin install swarm-coordination
/plugin install consensus-protocols
/plugin install hive-mind-orchestration
```

### For Full-Stack Developers

```bash
/plugin install core-dev-suite
/plugin install testing-qa-framework
/plugin install api-docs-generator
```

### For Agentic Development

```bash
/plugin install modular-agentic-dev
/plugin install sparc-methodology
/plugin install memory-coordination
```

## 🔧 Configuration

Most plugins work out of the box. Some require environment variables:

### Trading Plugins

```bash
EXCHANGE_API_KEY=your_key
EXCHANGE_SECRET=your_secret
PAPER_TRADING=true
```

### GitHub Plugins

```bash
GITHUB_TOKEN=your_github_token
GITHUB_ORG=your_org  # optional
```

## 📖 Documentation

Each plugin includes:

- Detailed agent descriptions
- Workflow examples
- Configuration guides
- Usage patterns

Access documentation:

```bash
/plugin info <plugin-name>
```

## 🏗️ Architecture

All plugins reference the source code in [jmanhype/multi-agent-system](https://github.com/jmanhype/multi-agent-system):

```
multi-agent-system/
├── .claude/
│   ├── agents/       # 68+ specialized agents
│   ├── commands/     # 75+ slash commands
│   ├── workflows/    # 6 workflow templates
│   ├── hooks/        # 8 execution hooks
│   └── helpers/      # 9 setup scripts
```

### Plugin Structure

Each plugin is a curated subset of agents designed for specific workflows:

- **Focused agent selection** - Only the agents needed for the use case
- **Pre-configured workflows** - Ready-to-use command compositions
- **Domain-specific hooks** - Automated safety and validation
- **Minimal dependencies** - Fast installation and updates

## 🤝 Contributing

We welcome contributions! Ways to help:

1. **Report Issues** - Found a bug? [Open an issue](https://github.com/jmanhype/claude-code-plugins/issues)
2. **Suggest Plugins** - Have ideas for new plugins? Let us know!
3. **Improve Docs** - Help make our docs better
4. **Share Use Cases** - Show us what you built!

## 📜 License

MIT License - see [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

Built on:

- [Claude Code](https://docs.claude.com/en/docs/claude-code) by Anthropic
- [DSPy](https://github.com/stanfordnlp/dspy) by Stanford NLP
- [CCXT](https://github.com/ccxt/ccxt) for crypto exchange integration

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/jmanhype/claude-code-plugins/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jmanhype/claude-code-plugins/discussions)
- **Source**: [Multi-Agent System](https://github.com/jmanhype/multi-agent-system)

---

**Made with 🧊 by [@jmanhype](https://github.com/jmanhype)**
