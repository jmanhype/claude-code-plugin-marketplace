# Changelog

All notable changes to the LLM Trading Pipeline and QTS system will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-26

### Added

#### Core QTS Trading System
- **LLM Client** (`qts/llm_client.py`)
  - LocalHeuristicLLM mock for testing with deterministic seeded RNG
  - OpenAI GPT-4 integration with JSON response format
  - DeepSeek API integration
  - Fail-safe NO_TRADE on errors

- **Risk Manager** (`qts/risk.py`)
  - Multi-layer risk validation with per-symbol and gross leverage caps
  - Mandatory stop-loss validation (0.5-5%, ATR×1.5)
  - Position sizing limits (25% per symbol, 100% gross notional)
  - Daily loss limit (-5%) with auto-flatten and 60-minute cooldown
  - Maximum drawdown circuit breaker (-10%)
  - Order rate limiting (30 orders/minute)
  - Comprehensive violation tracking and logging

- **Trade Executor** (`qts/executor.py`)
  - PaperExecutor with realistic slippage simulation (20 bps tolerance)
  - LiveExecutor with CCXT integration (disabled by default, requires explicit approval)
  - Latency tracking and fill price simulation

- **ACE Bullet Logger** (`qts/bullets.py`)
  - State→Action→Result logging for every trading decision
  - Regime classification (volatility, trend, liquidity)
  - Graph edges (led_to, confirmed_by, invalidated_by, same_regime_as)
  - JSON storage with querying and statistics

- **Main Runner** (`qts/main.py`)
  - Single-tick execution orchestrating LLM → Risk → Executor → Bullets
  - CLI with dry-run mode, multiple LLM providers, and paper/live modes
  - Comprehensive summary statistics

- **Tournament System** (`qts/tournament.py`)
  - Multi-variant paper trading with same prompt, different exit strategies
  - Daily leaderboard tracking (PnL, Sharpe, Sortino, MDD, hit rate, violations)
  - Objective promotion gate with 4-week criteria
  - Deterministic seeded RNG per variant for reproducible results
  - JSON output for analysis

#### Configuration & Prompts
- **Canonical Intraday Prompt** (`prompts/canonical_intraday_prompt.md`)
  - Strict JSON output format with decision, actions, stop_loss, leverage, rationale
  - R:R ≥2:1 requirement with mandatory stop-loss
  - Three detailed examples (long, short, NO_TRADE)
  - 220-character rationale limit

- **Risk Configuration** (`config/qts.risk.json`)
  - Comprehensive risk parameters with inline documentation
  - Leverage caps: 1.5x BTC/ETH, 1.2x others, 1.0x gross
  - Notional limits: 25% per symbol, 100% gross
  - Stop-loss bounds: 0.5-5%
  - Loss limits and cooldowns

#### Security Framework
- **Plugin Schema** (`schemas/plugin.schema.json`)
  - Validation for plugin manifests with semver enforcement
  - New permissions model: filesystem, network, exec, env, trading
  - Remote source pinning and integrity hash requirements

- **Signal Graph Schema** (`schemas/signal-graph.schema.json`)
  - ACE bullet validation with state→action→result structure
  - Regime and edge validation

- **Plugin Validator** (`tools/validate_plugins.py`)
  - CI-ready validator with schema compliance checks
  - Detection of unpinned remote sources (flags /main/ URLs)
  - Integrity hash verification for remote sources
  - Trading plugin risk config validation

- **Security Policy** (`SECURITY.md`)
  - Comprehensive threat model and supply-chain attack prevention
  - Remote source pinning requirements with commit SHA examples
  - Hook sandboxing recommendations
  - Trading approval workflow (paper → tournament gate → guarded live)
  - Secrets management best practices
  - Incident response procedures

- **CI Workflow Documentation** (`CI_WORKFLOW_NOTE.md`)
  - GitHub Actions setup instructions for plugin validation
  - Workflow requires `workflows` permission to push

#### Plugins
- **tournament-runner** (NEW)
  - Paper tournament orchestration plugin
  - Permissions: filesystem, env, trading:paper (exec:false for security)
  - Comprehensive README with usage and promotion criteria

- **quant-trading-system** (UPDATED)
  - Added permissions: filesystem, network, env, trading:paper
  - Added riskConfigPath: config/qts.risk.json

- **research-execution-pipeline** (UPDATED)
  - Added permissions: filesystem, env, trading:none
  - Added promptPath: prompts/canonical_intraday_prompt.md

#### Documentation
- `requirements.txt` - Python dependencies (jsonschema, optional: openai, ccxt)
- Plugin READMEs with permissions, usage, and safety notes

### Fixed

#### Critical Bugs (from PR review)
- **ExecutionResult initialization**: Added default `success=False` to prevent TypeError at runtime
- **Notional calculation**: Removed erroneous price multiplication (size is already fraction of equity)
  - Before: `notional = size * equity * leverage * price` ❌
  - After: `notional = size * equity * leverage` ✅
  - Impact: Risk checks now work correctly; previously all trades were rejected
- **Sortino ratio calculation**: Fixed denominator to use total returns count instead of only downside returns
  - Aligns with standard Sortino formula
- **Leverage/notional config mismatch**: Changed `leverage_gross` from 1.5 to 1.0
  - Resolves logical contradiction with `notional_gross: 1.0`
  - Ensures consistent 100% equity exposure limit

#### Security Fixes
- **tournament-runner exec permission**: Changed from `exec:true` to `exec:false`
  - Reduces command injection attack surface
  - No shell execution needed for tournament

### Changed

#### Improvements (from PR review)
- **Deterministic RNG per variant**: Each tournament variant now uses seeded RNG based on name hash
  - Ensures fair comparisons across variants
  - Reproducible results: same variant always produces same metrics
  - Seed: `hash(variant.name) % (2^32)`
- **Defensive guard for execution result**: Safe access to `execution_result['success']` in summary
  - Prevents KeyError if result is None or malformed
  - Uses `isinstance()` check and `.get()` method

### Documentation Updates
- **tournament-runner README**: Added Reproducibility section explaining deterministic RNG
- **tournament-runner README**: Updated Permissions section to reflect exec:false
- **CHANGELOG.md**: Created comprehensive changelog (this file)

### Known Limitations

#### Tournament Simulation (v1)
- Currently uses simplified mock simulation with random trades
- Does NOT integrate with real trading pipeline or historical data
- **Rationale**: Real integration requires:
  - Historical market data feed infrastructure
  - Refactoring `main.py` into reusable `TradingPipeline` class
  - Time-series simulation framework
- **Future**: Consider enhancement for v2 with full pipeline integration

### Migration Guide

#### For Existing Users
No migration needed - this is the initial release.

#### Risk Configuration
If you customize `config/qts.risk.json`, note that:
- `leverage_gross` is now 1.0 (was 1.5 in early drafts)
- This aligns with `notional_gross: 1.0` for consistent 100% equity limit
- Per-symbol leverage can still be 1.5x (BTC/ETH) or 1.2x (others)

### Security Notes

⚠️ **Live Trading**
- Disabled by default in all executors
- Requires THREE approvals:
  1. Explicit `enabled=True` flag in code
  2. `"trading": "live"` in plugin permissions
  3. Manual approval after passing 4-week promotion gate
- Start with 1% of paper size for guarded rollout

⚠️ **Existing Plugins**
- Many existing marketplace plugins have unpinned remote sources
- Validator flags these (uses `/main/` instead of commit SHA)
- Security framework applies to NEW plugins
- Existing plugins should be updated incrementally

⚠️ **Secrets**
- Never commit API keys to version control
- Use environment variables: `EXCHANGE_API_KEY`, `EXCHANGE_SECRET`
- Consider OS keychain or secret management tools (1Password CLI, Vault)

### Testing

Run validation locally:
```bash
pip install jsonschema
python tools/validate_plugins.py
```

Test single-tick (dry-run):
```bash
PYTHONPATH=. python -m qts.main --symbols ETH SOL --llm-provider mock --dry-run
```

Run 7-day paper tournament:
```bash
PYTHONPATH=. python -m qts.tournament --variants tp_trail_1.0 tp_trail_1.5 --days 7
```

Check promotion gate:
```bash
PYTHONPATH=. python -m qts.tournament --check-gate tp_trail_1.5 --gate-weeks 4
```

### Credits

Built with [Claude Code](https://claude.com/claude-code)

---

## [Unreleased]

### Planned
- Historical data integration for tournaments
- Hyperliquid connector (if CCXT insufficient)
- Dashboard for PnL/Sharpe/MDD visualization
- Automatic weekly promotion review doc generation
- Real LLM integration (DeepSeek/OpenAI) testing
- Multi-timeframe support (currently intraday only)
