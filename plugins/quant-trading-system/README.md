# Quantitative Trading System Plugin

Complete production-grade quantitative trading stack for cryptocurrency markets.

## Features

### 🛡️ Safety First
- **Circuit Breaker** - Automatic failover to paper trading on risk/latency errors
- **Kill Switch** - Emergency stop all trading with one command
- **Approval Guards** - Manual approval required for live trades
- **Pre-trade Validation** - Risk checks before every execution

### 📊 Trading Infrastructure
- **Risk Manager** - Multi-layer risk validation and position sizing
- **CCXT Integration** - Support for 100+ cryptocurrency exchanges
- **Metrics Tracking** - Comprehensive trade logging and analytics
- **Paper/Live Modes** - Safe testing before going live

### 🔄 Automated Workflows
- **5-Minute Loop** - Continuous trading execution (configurable)
- **Pre-Trade Hooks** - Validation, risk checks, approvals
- **Post-Trade Hooks** - Logging, metrics, notifications

## Installation

```bash
/plugin install quant-trading-system
```

## Configuration

### Required Environment Variables
```bash
EXCHANGE_API_KEY=your_api_key
EXCHANGE_SECRET=your_api_secret
```

### Optional Configuration
```bash
PAPER_TRADING=true              # Default: true (safe mode)
TRADE_INTERVAL=5                # Minutes between trades
MAX_POSITION_SIZE=1000          # Maximum position size in USD
RISK_LIMIT_PERCENT=2            # Max risk per trade (%)
```

## Usage

### Paper Trading (Safe)
```bash
# Hooks automatically enforce paper mode without PIN
/crypto-trader start
```

### Live Trading (Requires Approval)
```bash
# Set environment
export PAPER_TRADING=false

# Start trading (will prompt for PIN via guard_approve.sh)
/crypto-trader start
```

### Emergency Stop
```bash
# Immediately halt all trading
.claude/hooks/kill_switch.sh
```

### Circuit Breaker
The circuit breaker automatically triggers when:
- Risk limits exceeded
- API latency > threshold
- Unexpected errors occur
- Loss limit reached

Status: Automatically flips to paper trading mode

## Hooks

### pre_trade.sh
Runs before every trade:
- Validates exchange connection
- Checks risk limits
- Verifies API keys
- Requires approval for live trades

### post_trade.sh
Runs after every trade:
- Logs trade details to `logs/trades.jsonl`
- Updates metrics database
- Calculates P&L
- Sends notifications (if configured)

### circuit_breaker.sh
Continuously monitors:
- API latency
- Error rates
- Position sizes
- P&L thresholds

Auto-recovery: Resumes paper trading after cooldown

## Commands

### /ccxt-exchange
CCXT exchange operations:
```bash
/ccxt-exchange balance           # Check account balance
/ccxt-exchange ticker BTC/USDT   # Get ticker data
/ccxt-exchange markets           # List available markets
```

### /metrics-write
Write custom metrics:
```bash
/metrics-write trade_count 42
/metrics-write total_pnl 1250.50
```

## Safety Checklist

Before going live:

- [ ] Test in paper mode for 7+ days
- [ ] Verify risk limits are appropriate
- [ ] Set up kill switch access
- [ ] Configure notification alerts
- [ ] Review circuit breaker thresholds
- [ ] Backup API keys securely
- [ ] Document emergency procedures

## Workflows

### crypto-trader.md
5-minute trading loop:
1. Fetch market data
2. Run strategy signals
3. Pre-trade validation
4. Execute trades
5. Post-trade logging
6. Sleep until next interval

### quant-trading-workflow.md
Complete workflow:
1. Research phase (DSPy optimization)
2. Backtesting
3. Paper trading validation
4. Gradual live deployment
5. Continuous monitoring

## Risk Management

The risk-manager agent enforces:
- **Position Sizing** - Kelly Criterion or fixed %
- **Stop Losses** - Automatic exit on loss threshold
- **Take Profits** - Lock in gains at targets
- **Exposure Limits** - Max total portfolio risk
- **Correlation Limits** - Avoid concentrated risk

## Troubleshooting

### Trade Rejected
Check:
1. `pre_trade.sh` logs in `.claude/hooks/logs/`
2. Risk limits in configuration
3. Exchange API connectivity
4. Account balance

### Circuit Breaker Triggered
1. Check `.claude/hooks/logs/circuit_breaker.json`
2. Review error messages
3. Wait for cooldown period
4. Restart in paper mode
5. Investigate root cause

### Kill Switch Activated
1. All positions immediately closed
2. All orders cancelled
3. System halted
4. Manual intervention required to restart

## Examples

### Basic Setup
```bash
# Install plugin
/plugin install quant-trading-system

# Configure
export EXCHANGE_API_KEY=xxx
export EXCHANGE_SECRET=yyy
export PAPER_TRADING=true

# Start paper trading
/crypto-trader start
```

### Production Deployment
```bash
# After successful paper trading
export PAPER_TRADING=false
export MAX_POSITION_SIZE=500
export RISK_LIMIT_PERCENT=1

# Start with approval guard
/crypto-trader start
# (Will prompt for PIN approval)
```

## Monitoring

Logs stored in:
```
.claude/hooks/logs/
├── trades.jsonl          # All trades
├── circuit_breaker.json  # Circuit breaker events
├── pre_trade.json        # Pre-trade validations
└── post_trade.json       # Post-trade results
```

Metrics database:
```
db/metrics.db             # SQLite database
```

## Support

- **Issues**: [GitHub Issues](https://github.com/jmanhype/multi-agent-system/issues)
- **Docs**: [Trading Workflows](https://github.com/jmanhype/multi-agent-system/tree/main/.claude/workflows)
- **Source**: [Multi-Agent System](https://github.com/jmanhype/multi-agent-system)
