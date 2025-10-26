# QTS Complete Integration Guide
**All 3 Plugins Working Together**

This guide shows how to use the complete autonomous trading system with all 3 plugins integrated:

1. **quant-trading-system** (QTS Core): Risk-managed execution with ACE logging
2. **market-intelligence**: Real-time CCXT market data with order book analysis
3. **research-execution-pipeline**: Autonomous strategy discovery via DSPy/GEPA

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [System Architecture](#system-architecture)
3. [Installation](#installation)
4. [Usage Modes](#usage-modes)
5. [Configuration](#configuration)
6. [Workflows](#workflows)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Option 1: Test Mode (No API Keys Required)
```bash
# Test all components with mock data
python qts_orchestrator.py --mode test

# Output:
# ✅ Execution test passed
# ✅ Tournament test passed
# 🎉 System working!
```

### Option 2: Full Autonomous Mode (Requires OpenAI API Key)
```bash
# Set API key
export OPENAI_API_KEY=your_key_here

# Run complete autonomous workflow
python qts_orchestrator.py --mode autonomous --llm-provider openai

# This will:
# 1. Analyze recent trading data
# 2. Use DSPy to generate new strategies
# 3. Run tournament to validate them
# 4. Execute the best strategy
```

---

## System Architecture

### Complete Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: Research Loop (DSPy Strategy Discovery)           │
│  • Analyze ACE bullets from recent trades                   │
│  • Identify winning/losing patterns                         │
│  • Generate new strategy variants via DSPy                  │
│  • Optimize prompts using GEPA                              │
│  • Write new prompts to prompts/ directory                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: Tournament Validation                             │
│  • Test all strategy variants on recent data                │
│  • Calculate Sharpe, drawdown, win rate                     │
│  • Rank strategies by performance                           │
│  • Select winner via promotion gates                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: Live Execution (with Market Intelligence)         │
│  • Fetch real-time CCXT market data                         │
│  • LLM generates trading decisions                          │
│  • Risk manager validates (leverage, stop loss, etc)        │
│  • Execute trades (paper/live)                              │
│  • Log ACE bullets for next research cycle                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
                        (Loop back to Phase 1)
```

### Plugin Responsibilities

| Plugin | Purpose | Key Features |
|--------|---------|--------------|
| **quant-trading-system** | Core execution engine | Risk management, ACE logging, paper/live trading |
| **market-intelligence** | Enhanced market data | Real CCXT data, order book depth, volatility analysis |
| **research-execution-pipeline** | Autonomous learning | DSPy strategy discovery, GEPA optimization, daily research loops |

---

## Installation

### 1. Core Dependencies

```bash
# Already installed from previous steps:
pip install ccxt requests         # Market intelligence
pip install dspy-ai openai        # Research pipeline
```

### 2. Verify Installation

```bash
# Test that everything works
python qts_orchestrator.py --mode test

# Expected output:
# ✅ Execution complete
# ✅ Tournament complete
# ✅ TEST COMPLETE
```

### 3. Optional: Set Up Daily Research Loop

Add to crontab for daily strategy discovery:

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 6 AM)
0 6 * * * cd /path/to/qts && /usr/bin/python qts_orchestrator.py --mode autonomous --llm-provider openai >> logs/cron.log 2>&1
```

---

## Usage Modes

The orchestrator supports 5 different modes:

### Mode 1: Test (Default)
Quick validation of all components with mock data.

```bash
python qts_orchestrator.py --mode test
```

**What it does:**
- Runs single trade execution with mock LLM
- Runs 1-day tournament
- Uses mock market data
- No API keys required

**When to use:** First-time setup, testing changes

---

### Mode 2: Research Only
Generate new strategies from recent trading data.

```bash
export OPENAI_API_KEY=your_key
python qts_orchestrator.py --mode research --days 7 --llm-provider openai
```

**What it does:**
- Analyzes last 7 days of ACE bullets
- Uses DSPy to identify patterns
- Generates new strategy variants
- Writes new prompts to `prompts/`

**When to use:** You want new strategy ideas, manual strategy iteration

---

### Mode 3: Tournament Only
Validate existing strategies.

```bash
python qts_orchestrator.py --mode tournament --days 3
```

**What it does:**
- Backtests all prompt variants in `prompts/`
- Calculates performance metrics
- Ranks by Sharpe ratio
- Saves results to `logs/tournament/`

**When to use:** Compare strategy performance, find best variant

---

### Mode 4: Execute Only
Run best strategy from tournament.

```bash
python qts_orchestrator.py --mode execute --symbols BTC ETH SOL \
  --llm-provider openai --execution-mode paper
```

**What it does:**
- Uses tournament winner (or default prompt)
- Fetches market data (real if `--use-market-intelligence`)
- Executes trades via LLM decisions
- Logs ACE bullets

**When to use:** Production trading, manual execution

---

### Mode 5: Autonomous (Full Workflow)
Complete research → tournament → execution loop.

```bash
export OPENAI_API_KEY=your_key
python qts_orchestrator.py --mode autonomous \
  --days 7 \
  --symbols BTC ETH \
  --llm-provider openai \
  --execution-mode paper
```

**What it does:**
1. Research: Analyze 7 days of data → generate new strategies
2. Tournament: Validate all strategies → pick winner
3. Execute: Trade with best strategy → log ACE bullets

**When to use:** Fully autonomous trading, daily production runs

---

## Configuration

### 1. LLM Provider

Choose which LLM to use for decisions:

```bash
# Mock LLM (fast, free, heuristic decisions)
python qts_orchestrator.py --llm-provider mock

# OpenAI GPT-4 (requires OPENAI_API_KEY)
export OPENAI_API_KEY=sk-...
python qts_orchestrator.py --llm-provider openai

# DeepSeek (requires DEEPSEEK_API_KEY)
export DEEPSEEK_API_KEY=sk-...
python qts_orchestrator.py --llm-provider deepseek
```

### 2. Market Data Source

Choose between mock data and real CCXT:

```bash
# Mock data (default, fast, no exchange required)
python qts_orchestrator.py --use-mock-data

# Real CCXT data (requires internet, exchange API)
python qts_orchestrator.py  # Real data is default
```

### 3. Execution Mode

Choose paper trading or live execution:

```bash
# Paper trading (simulated, no real money)
python qts_orchestrator.py --execution-mode paper

# Live trading (REAL MONEY - use with caution!)
python qts_orchestrator.py --execution-mode live
```

### 4. Risk Configuration

Edit `config/qts.risk.json` to adjust risk limits:

```json
{
  "leverage_btc_eth": 3,
  "leverage_other": 2,
  "notional_per_symbol": 10000,
  "daily_loss_limit": 0.05,
  "max_drawdown": 0.15,
  "min_stop_pct": 0.01,
  "max_stop_pct": 0.10
}
```

See `qts/risk.py` for full configuration options.

---

## Workflows

### Workflow 1: Daily Autonomous Trading

**Goal:** Continuously improve strategies and trade automatically.

**Setup:**
```bash
# 1. Set up cron job for daily research
crontab -e

# 2. Add this line (runs at 6 AM daily)
0 6 * * * cd /path/to/qts && python qts_orchestrator.py --mode autonomous --llm-provider openai --execution-mode paper >> logs/cron.log 2>&1

# 3. Monitor logs
tail -f logs/orchestrator.log
```

**What happens:**
- Every day at 6 AM:
  - Analyzes yesterday's trades
  - Generates new strategy ideas via DSPy
  - Runs tournament to validate
  - Executes best strategy
  - Logs ACE bullets for tomorrow

**Continuous improvement loop! 🔄**

---

### Workflow 2: Manual Strategy Development

**Goal:** Manually iterate on strategy ideas using tournament validation.

**Steps:**
```bash
# 1. Create new strategy prompt
cat > prompts/my_breakout_strategy.md <<'EOF'
You are a breakout trader.

Strategy:
- Enter on strong momentum (price > MA + 2*ATR)
- Stop loss at MA
- Take profit at 3:1 reward:risk

Risk: 2% per trade max
EOF

# 2. Run tournament to validate
python qts_orchestrator.py --mode tournament --days 7

# 3. Check results
cat logs/tournament/tournament_*.json | jq .

# 4. Iterate based on results
# - If good performance: use it!
# - If poor performance: revise prompt and repeat
```

---

### Workflow 3: Research-Driven Discovery

**Goal:** Let DSPy discover new strategies automatically.

**Steps:**
```bash
# 1. Accumulate trading data (run for a week)
for i in {1..7}; do
  python qts_orchestrator.py --mode execute --llm-provider openai
  sleep 86400  # Wait 1 day
done

# 2. Run research loop
python qts_orchestrator.py --mode research --days 7 --llm-provider openai

# 3. Check new strategies
ls -lt prompts/
# You should see new strategy files generated

# 4. Validate via tournament
python qts_orchestrator.py --mode tournament --days 7

# 5. Use best strategy
python qts_orchestrator.py --mode execute --llm-provider openai
```

---

### Workflow 4: Real CCXT Market Data

**Goal:** Use real exchange data for better decisions.

**Setup:**
```bash
# 1. Install CCXT (already done if you followed installation)
pip install ccxt

# 2. Run with market intelligence enabled
python qts_orchestrator.py --mode execute \
  --llm-provider openai \
  --symbols BTC ETH \
  # Real data is default, but you can explicitly disable mock:
  # (remove --use-mock-data flag)
```

**Market intelligence provides:**
- Real-time price (bid/ask)
- Order book depth and imbalance
- 24h volume and volatility
- Spread analysis

**Example LLM context:**
```
Market Data for BTC (binance):
- Price: $49,823.45 (Bid: $49,820.00, Ask: $49,827.00)
- 24h Change: +2.34% (High: $50,200.00, Low: $48,500.00)
- Spread: 0.014%
- Volatility: 1.89%
- Order Book Imbalance: +0.023 (Bullish)
- Liquidity: Bids $12,345,678 / Asks $11,987,654
- Volume 24h: $987,654,321
```

This rich data helps the LLM make better decisions!

---

### Workflow 5: Tournament-Driven Selection

**Goal:** Compare multiple strategies and pick the winner.

**Setup:**
```bash
# 1. Create multiple strategy variants
# (Already have 3 variants in prompts/)

# 2. Run tournament
python qts_orchestrator.py --mode tournament --days 7

# 3. View leaderboard
tail -20 logs/tournament/tournament_*.json

# Example output:
# Rank  Variant             Trades    PnL%      Sharpe    MDD%      Hit%
# 1     tp_trail_2.0        35        8.67%     4.23      -2.1%     51.4%
# 2     tp_trail_1.5        35        5.12%     2.87      -3.4%     48.6%
# 3     tp_trail_1.0        35        1.23%     0.94      -5.2%     45.7%

# 4. Use winner for production
python qts_orchestrator.py --mode execute --llm-provider openai
# (automatically uses tournament winner)
```

---

## Monitoring

### 1. Real-Time Logs

```bash
# Watch orchestrator logs
tail -f logs/orchestrator.log

# Watch execution logs
tail -f logs/bullets/*.json

# Watch tournament results
ls -lt logs/tournament/
```

### 2. ACE Bullets

Each trade generates an ACE bullet in `logs/bullets/`:

```json
{
  "timestamp": "2025-10-26T15:52:38.156789",
  "symbol": "BTC",
  "market_data": {
    "price": 49290.02,
    "atr": 1566.10,
    "volume": 123456789
  },
  "llm_decision": {
    "decision": "TRADE",
    "actions": [{
      "symbol": "BTC",
      "type": "long",
      "size": 0.1
    }],
    "rationale": "Strong breakout above resistance..."
  },
  "risk_check": {
    "approved": true,
    "violations": []
  },
  "execution_result": {
    "success": true,
    "fills": [...]
  }
}
```

### 3. Tournament Results

Tournament results saved to `logs/tournament/tournament_YYYYMMDD_HHMMSS.json`:

```json
{
  "timestamp": "2025-10-26T15:52:38",
  "variants": [
    {
      "name": "tp_trail_2.0",
      "total_pnl": 8.67,
      "sharpe": 4.23,
      "max_drawdown": -2.1,
      "win_rate": 51.4,
      "trades": 35
    }
  ],
  "winner": "tp_trail_2.0"
}
```

### 4. Research Results

Research loop results saved to `logs/research_results.jsonl`:

```json
{
  "timestamp": "2025-10-26T06:00:00",
  "insights": "Trailing stop strategies perform better in volatile markets...",
  "improvements": "Consider tighter stops on BTC, wider on altcoins...",
  "new_variant_name": "adaptive_trail_volatility_20251026",
  "new_prompt_path": "prompts/adaptive_trail_volatility_20251026.md"
}
```

---

## Troubleshooting

### Issue 1: CCXT Not Installed

**Error:**
```
ccxt not installed - market intelligence will use mock data
```

**Fix:**
```bash
pip install ccxt
```

**Note:** System will gracefully fall back to mock data if CCXT unavailable.

---

### Issue 2: OpenAI API Key Not Set

**Error:**
```
ERROR: OPENAI_API_KEY environment variable not set
```

**Fix:**
```bash
export OPENAI_API_KEY=sk-your-key-here

# Or add to ~/.bashrc for persistence:
echo 'export OPENAI_API_KEY=sk-your-key-here' >> ~/.bashrc
source ~/.bashrc
```

---

### Issue 3: Risk Config Error

**Error:**
```
RiskConfig.__init__() got an unexpected keyword argument '_comment'
```

**Fix:**
This is already fixed! The system now filters out comment fields (those starting with `_`) from `config/qts.risk.json`.

If you still see this error, ensure you're using the latest code:
```bash
git pull origin claude/qts-market-intelligence-setup-011CUW4wQ8xzCQtdLUMBX2pj
```

---

### Issue 4: No Tournament Results

**Error:**
```
WARNING: Tournament completed but no results found
```

**Cause:** Tournament saves to `logs/tournament/` but orchestrator looks in `qts_tournament/`.

**Fix:**
```bash
# Create symlink (temporary fix)
ln -s logs/tournament qts_tournament

# Or update orchestrator to use correct path
# (This will be fixed in next version)
```

---

### Issue 5: DSPy Import Error

**Error:**
```
ModuleNotFoundError: No module named 'dspy'
```

**Fix:**
```bash
pip install dspy-ai
```

---

## Advanced Configuration

### Custom Research Loop Schedule

Edit the research loop frequency by modifying the GEPA optimization settings in `qts/research_loop.py`:

```python
# Run GEPA optimization with custom iterations
loop = ResearchLoop(llm_model="gpt-4")
loop.optimize_with_gepa(
    training_data=my_training_data,
    iterations=20  # Default is 10
)
```

### Custom Market Intelligence Exchanges

By default, the system uses Binance. To use a different exchange:

```python
# In qts/main.py, modify fetch_market_data():
mi = get_market_intelligence(
    exchange="kraken",  # Or: coinbase, bitfinex, etc
    testnet=True
)
```

See [CCXT supported exchanges](https://github.com/ccxt/ccxt#supported-cryptocurrency-exchange-markets) for full list.

### Custom Promotion Gates

Edit tournament promotion criteria in `qts/tournament.py`:

```python
# Modify promotion gate thresholds
PROMOTION_GATES = {
    "min_sharpe": 2.0,      # Default: 1.5
    "max_drawdown": 0.10,   # Default: 0.15
    "min_trades": 20,       # Default: 10
    "min_win_rate": 0.45    # Default: 0.40
}
```

---

## Summary

You now have a complete autonomous trading system with:

✅ **QTS Core**: Risk-managed execution with ACE logging
✅ **Market Intelligence**: Real CCXT market data
✅ **Research Pipeline**: Autonomous strategy discovery via DSPy

**Complete workflow:**
1. Daily research discovers new strategies
2. Tournament validates them
3. Best strategy executes trades
4. ACE bullets logged for next research cycle
5. **Continuous improvement! 🚀**

---

## Quick Reference

```bash
# Test all components
python qts_orchestrator.py --mode test

# Full autonomous mode
export OPENAI_API_KEY=sk-...
python qts_orchestrator.py --mode autonomous --llm-provider openai

# Just research
python qts_orchestrator.py --mode research --days 7 --llm-provider openai

# Just tournament
python qts_orchestrator.py --mode tournament --days 3

# Just execute
python qts_orchestrator.py --mode execute --symbols BTC ETH --llm-provider openai

# Daily cron job (add to crontab -e)
0 6 * * * cd /path/to/qts && python qts_orchestrator.py --mode autonomous --llm-provider openai >> logs/cron.log 2>&1
```

---

## Next Steps

1. **Start small:** Run in test mode, then paper trading
2. **Accumulate data:** Let it run for 1-2 weeks to build ACE bullet history
3. **Research loop:** Use DSPy to discover new strategies
4. **Tournament validate:** Compare strategies objectively
5. **Iterate:** Refine based on results
6. **Scale up:** Gradually increase position sizes as confidence grows

**Happy trading! 📈**
