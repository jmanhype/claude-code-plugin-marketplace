# QTS Usage Guide

Complete guide to using the Quantitative Trading System (QTS).

## Quick Start

### 1. Basic Paper Trading

Run a single-tick paper trading test with mock data:

```bash
# Single tick with default symbols (ETH, SOL, XRP, BTC, DOGE, BNB)
PYTHONPATH=. python -m qts.main --llm-provider mock

# Custom symbols
PYTHONPATH=. python -m qts.main --symbols BTC ETH --llm-provider mock
```

### 2. With Real Market Data

Enable real CCXT market data:

```bash
# Requires: pip install ccxt
PYTHONPATH=. python -m qts.main \
  --symbols BTC ETH SOL \
  --llm-provider mock \
  --use-market-intelligence
```

### 3. With Real LLM Provider

Use OpenAI, DeepSeek, Anthropic, or Gemini:

```bash
# Set API key
export OPENAI_API_KEY=sk-...

# Run with OpenAI
PYTHONPATH=. python -m qts.main \
  --symbols BTC ETH \
  --llm-provider openai \
  --execution-mode paper
```

## Configuration

### Risk Configuration

Create a custom risk config file (e.g., `config/my_risk.json`):

```json
{
  "_comment": "Custom risk parameters",
  "leverage_btc_eth": 1.5,
  "leverage_other": 1.2,
  "leverage_gross": 1.5,
  "notional_per_symbol": 0.25,
  "notional_gross": 1.0,
  "min_stop_pct": 0.005,
  "max_stop_pct": 0.05,
  "atr_multiplier": 1.5,
  "daily_loss_limit": -0.05,
  "daily_loss_cooldown_min": 60,
  "max_drawdown": -0.10,
  "max_orders_per_min": 30,
  "circuit_breaker_cooldown_min": 60
}
```

Use it:

```bash
PYTHONPATH=. python -m qts.main \
  --risk-config config/my_risk.json \
  --symbols BTC ETH
```

### Trading Prompt

Customize the trading strategy by editing `prompts/canonical_intraday_prompt.md`:

```bash
PYTHONPATH=. python -m qts.main \
  --prompt prompts/my_custom_prompt.md \
  --llm-provider openai
```

## API Usage

### Programmatic Trading

```python
from qts.llm_client import get_llm_client
from qts.risk import RiskManager, RiskConfig
from qts.executor import get_executor
from qts.bullets import BulletStore
from qts.main import run_tick, load_prompt

# Initialize components
llm_client = get_llm_client("mock")
risk_manager = RiskManager(RiskConfig())
executor = get_executor("paper")
bullet_store = BulletStore()
prompt = load_prompt()

# Run a tick
bullet = run_tick(
    symbol="BTC",
    llm_client=llm_client,
    risk_manager=risk_manager,
    executor=executor,
    bullet_store=bullet_store,
    prompt=prompt
)

print(f"Decision: {bullet.llm_decision['decision']}")
print(f"Risk approved: {bullet.risk_check['approved']}")
```

### Custom Risk Manager

```python
from qts.risk import RiskManager, RiskConfig, PortfolioState

# Create custom config
config = RiskConfig(
    leverage_btc_eth=2.0,  # More aggressive
    daily_loss_limit=-0.03  # Tighter stop
)

# Initialize with custom state
state = PortfolioState(
    equity=50000.0,
    peak_equity=50000.0,
    positions={"BTC": {"notional": 10000.0}}
)

manager = RiskManager(config, state)

# Check an order
result = manager.check_order(
    symbol="ETH",
    side="long",
    size=0.2,
    price=3000.0,
    leverage=1.5,
    stop_loss=0.015,
    atr=45.0
)

if result.approved:
    print("✓ Order approved")
else:
    print(f"✗ Rejected: {', '.join(result.messages)}")
```

### ACE Bullet Retrieval

```python
from qts.bullets import BulletStore

store = BulletStore()

# Load all bullets
bullets = store.load_all(limit=100)

# Query by symbol
btc_bullets = store.query(symbol="BTC", limit=50)

# Query by regime
high_vol_bullets = store.query(
    regime={"volatility": "high", "trend": "up"},
    limit=20
)

# Get statistics
stats = store.get_stats()
print(f"Total bullets: {stats['total']}")
print(f"Violations: {stats['violations']}")
```

## Advanced Features

### Tournament Mode

Run multi-variant paper trading tournaments:

```bash
# 7-day tournament with 3 strategy variants
PYTHONPATH=. python -m qts.tournament \
  --variants tp_trail_1.0 tp_trail_1.5 tp_trail_2.0 \
  --days 7 \
  --symbols BTC ETH SOL

# Check promotion gate (4-week validation)
PYTHONPATH=. python -m qts.tournament \
  --check-gate tp_trail_1.5 \
  --gate-weeks 4
```

### Research Loop

Automated daily research for strategy discovery:

```bash
# Run research loop (6am daily)
PYTHONPATH=. python -m qts.research_loop \
  --mode daily \
  --symbols BTC ETH SOL XRP
```

### Live Trading (Advanced)

⚠️ **WARNING: Live trading uses real money. Requires explicit approval.**

```bash
# Set exchange credentials
export EXCHANGE_API_KEY=your_key
export EXCHANGE_SECRET=your_secret

# Run on TESTNET first (recommended)
PYTHONPATH=. python -m qts.main \
  --execution-mode live \
  --symbols BTC \
  --llm-provider openai

# For production (requires approval process):
# 1. Complete 4-week tournament validation
# 2. Review risk parameters
# 3. Enable in code: LiveExecutor(enabled=True)
```

## Monitoring & Logging

### ACE Bullets

All decisions are logged as ACE bullets in `logs/bullets/`:

```bash
# View latest bullets
ls -lt logs/bullets/ | head -10

# Analyze a bullet
cat logs/bullets/bullet-2025-01-15-001.json | jq .
```

### Risk Violations

Check for violations:

```bash
# Count violations by type
jq '.result.violations[]' logs/bullets/*.json | sort | uniq -c
```

### Performance Metrics

```python
from qts.bullets import BulletStore

store = BulletStore()
bullets = store.load_all()

# Calculate metrics
total_trades = sum(1 for b in bullets if b.llm_decision['decision'] == 'TRADE')
rejected = sum(1 for b in bullets if not b.risk_check['approved'])
executed = sum(1 for b in bullets if b.execution_result and b.execution_result.get('success'))

print(f"Total trades attempted: {total_trades}")
print(f"Risk rejected: {rejected} ({rejected/total_trades*100:.1f}%)")
print(f"Successfully executed: {executed} ({executed/total_trades*100:.1f}%)")
```

## Testing

Run the test suite:

```bash
# Install pytest
pip install pytest

# Run all tests
pytest qts/test_risk.py -v

# Run specific test
pytest qts/test_risk.py::TestRiskManager::test_leverage_per_symbol_btc_eth -v
```

## Troubleshooting

### Common Issues

**1. "Risk config not found"**
```bash
# Create default config
mkdir -p config
cp examples/qts.risk.json config/
```

**2. "Prompt not found"**
```bash
# Create prompts directory
mkdir -p prompts
echo "You are a trading assistant..." > prompts/canonical_intraday_prompt.md
```

**3. "CCXT not installed"**
```bash
pip install ccxt
```

**4. "LLM API key not found"**
```bash
# Set environment variable
export OPENAI_API_KEY=sk-...
export DEEPSEEK_API_KEY=...
export ANTHROPIC_API_KEY=...
export GEMINI_API_KEY=...
```

## Safety Checklist

Before going live:

- [ ] Complete 4-week tournament validation
- [ ] Verify all risk limits are appropriate
- [ ] Test on exchange testnet/sandbox
- [ ] Monitor for 1 week with paper trading
- [ ] Set up alerting for violations
- [ ] Review circuit breaker thresholds
- [ ] Document approval process
- [ ] Enable live mode with `enabled=True`

## Support

- Issues: https://github.com/jmanhype/claude-code-plugins/issues
- Docs: See README.md and inline docstrings
- Examples: See `examples/` directory
