# claude-code-plugin-marketplace

Collection of 23 plugins for Claude Code. Each plugin is a directory under `plugins/` containing a `plugin.json` manifest, a `README.md`, and in some cases implementation code.

## Status

Mixed. Some plugins (quant-trading-system, code-safety-monitor, ace-context-engineering) contain implementation code. Most plugins are manifest + README definitions that describe agent prompts and workflows. No centralized test suite.

## Plugin Catalog (23)

| Plugin | Category | What It Contains |
|---|---|---|
| `ace-context-engineering` | Productivity | Schemas (7 JSON), scripts (5 Python), skill.md. Implements bullet/delta context evolution with TF-IDF retrieval. |
| `code-safety-monitor` | Safety | Python source in `src/`, `setup.py`, `requirements.txt`. DSPy-based backdoor detection. |
| `quant-trading-system` | Trading | Python modules in `qts/` at repo root (main, risk, executor, market_intelligence, tournament, research_loop, llm_client, bullets). |
| `tournament-runner` | Trading | Plugin manifest. Uses `qts.tournament` module from repo root. |
| `research-execution-pipeline` | Research | Plugin manifest. Uses `qts.research_loop` from repo root. |
| `modular-agentic-dev` | Methodology | Plugin manifest. Session-based agentic development framework. |
| `github-automation-suite` | GitHub | Plugin manifest. Describes 13 GitHub agent roles. |
| `swarm-coordination` | Distributed | Plugin manifest. Adaptive/hierarchical/mesh swarm patterns. |
| `consensus-protocols` | Distributed | Plugin manifest. Byzantine, Raft, CRDT, gossip protocols. |
| `core-dev-suite` | Development | Plugin manifest. Planner, coder, reviewer, tester, researcher agents. |
| `market-intelligence` | Trading | Plugin manifest. Market analysis agent definitions. |
| `repo-management-tools` | GitHub | Plugin manifest. Multi-repo coordination. |
| `hive-mind-orchestration` | Distributed | Plugin manifest. Distributed decision-making. |
| `testing-qa-framework` | Testing | Plugin manifest. TDD agents and test automation. |
| `api-docs-generator` | Documentation | Plugin manifest. OpenAPI/Swagger generation. |
| `cicd-automation` | DevOps | Plugin manifest. GitHub Actions automation. |
| `mobile-automation` | Mobile | Plugin manifest. React Native + ClassDojo workflows. |
| `performance-optimization` | Optimization | Plugin manifest. Load balancing and benchmarks. |
| `architecture-design` | Architecture | Plugin manifest. System design agents. |
| `memory-coordination` | Coordination | Plugin manifest. Memory and task orchestration. |
| `safety-compliance` | Safety | Plugin manifest. Circuit breakers and kill switches. |
| `sparc-methodology` | Methodology | Plugin manifest. SPARC development framework. |
| `base-template-generator` | Templates | Plugin manifest. Project scaffolding. |

## Repository Structure

```
.claude-plugin/
  marketplace.json       # Plugin registry (23 entries)

plugins/
  <plugin-name>/
    plugin.json          # Manifest (name, description, version)
    README.md            # Plugin documentation
    src/                 # (some plugins) Implementation code

qts/                     # Quantitative trading system (shared module)
  main.py                # Entry point
  risk.py                # Risk management (leverage caps, stop-loss, drawdown)
  executor.py            # Order execution (paper + live via CCXT)
  market_intelligence.py # Market data analysis
  tournament.py          # Multi-variant paper trading tournaments
  research_loop.py       # Strategy research pipeline
  llm_client.py          # LLM provider integration (mock, OpenAI, DeepSeek)
  bullets.py             # ACE bullet logging
```

## Installation

```bash
# Add marketplace to Claude Code
/plugin marketplace add jmanhype/claude-code-plugins

# Browse plugins
/plugin

# Install a specific plugin
/plugin install code-safety-monitor
```

## Quantitative Trading System

The `qts/` directory at the repo root contains the actual trading implementation shared by 3 plugins (quant-trading-system, tournament-runner, research-execution-pipeline).

```bash
# Paper trading
PYTHONPATH=. python -m qts.main --symbols ETH SOL XRP --llm-provider mock

# Tournament (multi-variant comparison)
PYTHONPATH=. python -m qts.tournament --variants tp_trail_1.0 tp_trail_1.5 --days 7
```

Risk defaults: 1.0x gross leverage cap, 25% max position per symbol, -5% daily loss limit, -10% max drawdown halt.

## Configuration

Trading plugins require environment variables:

```bash
EXCHANGE_API_KEY=...
EXCHANGE_SECRET=...
PAPER_TRADING=true   # default; live trading requires 3-layer approval
```

GitHub plugins require:

```bash
GITHUB_TOKEN=...
```

## Limitations

- Most plugins are manifest-only (prompt definitions, not executable code)
- The `/plugin` command infrastructure depends on Claude Code's plugin system, which is not publicly documented
- No tests for the plugin loading mechanism
- The `qts/` trading system has 1 test file (`test_risk.py`)
- Plugin versioning is inconsistent; only `ace-context-engineering` has a version field in the manifest
- No CI/CD pipeline for plugin validation
- The marketplace registry (`marketplace.json`) must be manually kept in sync with the `plugins/` directory
- Several GitHub Actions workflows reference external services that may not be configured
