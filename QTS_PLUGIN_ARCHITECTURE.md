# QTS Plugin Architecture - Complete Trading System

## 🏗️ The 3-Plugin Stack

You're absolutely right! The complete intraday LLM trading system uses **3 core plugins** that work together:

```
┌─────────────────────────────────────────────────────────────┐
│                   COMPLETE TRADING SYSTEM                    │
└─────────────────────────────────────────────────────────────┘

1. RESEARCH-EXECUTION-PIPELINE (Strategy Discovery)
   └─> Generates new trading strategies using DSPy/GEPA
       Daily research loop at 06:00
       Outputs: New canonical prompts

2. QUANT-TRADING-SYSTEM (Core Execution)
   └─> Executes strategies with risk management
       Market data → LLM → Risk → Execution → Logging
       Uses: Canonical prompts from research pipeline

3. MARKET-INTELLIGENCE (Market Data)
   └─> Provides market analysis and monitoring
       Enhanced CCXT exchange integration
       Feeds: Real-time data to QTS

4. TOURNAMENT-RUNNER (Validation)
   └─> Tests multiple strategy variants
       Promotion gates before live deployment
       Uses: QTS core for execution
```

---

## 📦 Plugin 1: Research-Execution Pipeline

**Purpose**: Automated strategy discovery and optimization

### What It Provides

**Agents**:
- `proposer-dspy` - DSPy-powered strategy proposal generation
- `strategy-finder` - Automated strategy discovery and evaluation

**Workflows**:
- `research-loop` - Daily 06:00 research loop generating new strategy candidates
- `research-workflow` - Complete research-execution workflow with GEPA optimization

**Commands**:
- `journal-append` - Append research findings to journal

**Hooks**:
- `verify_gate` - Verify strategy meets benchmark before promotion

### How It Works

```bash
# Daily at 06:00
1. DSPy proposes new strategy variants
2. Strategies are backtested/simulated
3. GEPA optimization improves prompts
4. Best performers promoted to tournament
5. New canonical_intraday_prompt.md generated
```

**Example Research Loop**:
```
06:00 - Research agent wakes up
     └─> Analyze last 24h of ACE bullets
     └─> Identify losing patterns
     └─> Propose 5 new strategy variants
     └─> Backtest on historical data
     └─> Generate optimized prompt for winner
     └─> Save to prompts/candidate_strategy_001.md
```

**Output**: New trading prompts that feed into QTS

---

## 📦 Plugin 2: Quant-Trading-System (QTS Core)

**Purpose**: Execute trading strategies with risk management

### What It Provides

**Core Modules** (What we just used!):
- `qts/main.py` - Trading loop
- `qts/risk.py` - Risk manager (9+ violation types)
- `qts/executor.py` - Paper/live execution
- `qts/llm_client.py` - LLM providers (mock/OpenAI/DeepSeek)
- `qts/bullets.py` - ACE bullet logging
- `qts/tournament.py` - Multi-variant testing

**Agents**:
- `risk-manager` - Multi-layer risk validation and position sizing

**Commands**:
- `ccxt-exchange` - CCXT exchange integration
- `metrics-write` - Write trading metrics to database

**Workflows**:
- `crypto-trader` - 5-minute crypto trading loop (paper/live)
- `quant-trading` - Complete quantitative trading workflow

**Hooks**:
- `pre_trade` - Pre-trade validation and risk checks
- `post_trade` - Post-trade logging and metrics
- `circuit_breaker` - Automatic circuit breaker for risk/latency errors
- `guard_approve` - Manual approval guard for live trading
- `kill_switch` - Emergency kill switch for all trading

**MCP**:
- `ccxt` - CCXT cryptocurrency exchange integration

### How It Works

```bash
# Every 5 minutes (or continuous)
PYTHONPATH=. python -m qts.main \
  --symbols ETH BTC SOL \
  --llm-provider openai \
  --execution-mode paper
```

**Pipeline**:
1. Fetch market data (price, ATR, MA20, volume)
2. LLM analyzes using canonical prompt → TRADE/NO_TRADE
3. Risk manager validates (leverage, sizing, stops)
4. Executor simulates/executes trade
5. ACE bullet logs complete state→action→result

**Input**: Canonical prompts (from research pipeline or manual)
**Output**: ACE bullets, executed trades, metrics

---

## 📦 Plugin 3: Market Intelligence

**Purpose**: Market analysis and monitoring

### What It Provides

**Agents**:
- `code-analyzer` - Advanced code quality analysis for market analysis tools

**Commands**:
- `ccxt-exchange` - CCXT exchange data and market intelligence

### How It Works

```bash
# Enhanced market data fetching
# Instead of mock data, use real CCXT data with additional indicators
```

**Enhancements**:
- Real-time order book depth
- Advanced technical indicators
- Multi-exchange price aggregation
- Volume-weighted average price (VWAP)
- Funding rate monitoring
- On-chain metrics (optional)

**Integration**:
- Replaces `fetch_market_data()` in `qts/main.py` with enhanced version
- Provides richer context to LLM for decision-making

---

## 🔄 How They Work Together

### Complete System Flow

```
┌──────────────────────────────────────────────────────────────┐
│ STEP 1: STRATEGY DISCOVERY (research-execution-pipeline)    │
└──────────────────────────────────────────────────────────────┘
Daily at 06:00:
├─> DSPy proposes new strategy variants
├─> Backtest on historical data
├─> GEPA optimization improves prompts
└─> Generate: prompts/candidate_strategy_001.md

┌──────────────────────────────────────────────────────────────┐
│ STEP 2: VALIDATION (tournament-runner + QTS core)           │
└──────────────────────────────────────────────────────────────┘
Week 1-6:
├─> Run tournament with candidate strategy
├─> Compare against current best (tp_trail_1.0)
├─> Track: Sharpe, Sortino, MDD, hit rate
└─> Check promotion gate (4-week criteria)

┌──────────────────────────────────────────────────────────────┐
│ STEP 3: EXECUTION (QTS core + market-intelligence)          │
└──────────────────────────────────────────────────────────────┘
Continuous (every 5 minutes):
├─> Market Intelligence: Fetch enhanced market data
├─> QTS: Send to LLM with canonical prompt
├─> QTS: Risk validation (9+ checks)
├─> QTS: Execute trade (paper/live)
└─> QTS: Log ACE bullet

┌──────────────────────────────────────────────────────────────┐
│ STEP 4: LEARNING (research-execution-pipeline)              │
└──────────────────────────────────────────────────────────────┘
Daily at 06:00:
├─> Analyze yesterday's ACE bullets
├─> Identify winning/losing patterns
├─> Propose improvements to strategy
└─> Cycle back to STEP 1
```

---

## 🚀 Production Setup with All 3 Plugins

### Install All Plugins

```bash
# Install plugin marketplace
/plugin marketplace add jmanhype/claude-code-plugin-marketplace

# Install all 3 trading plugins
/plugin install quant-trading-system
/plugin install research-execution-pipeline
/plugin install market-intelligence
/plugin install tournament-runner
```

### Day-to-Day Operation

#### Morning: Research (06:00)
```bash
# Automated via cron
0 6 * * * cd /path/to/project && /claude/workflows/research-loop.md

# This runs:
# 1. Analyze yesterday's bullets
# 2. Propose new strategies
# 3. Backtest candidates
# 4. Generate optimized prompts
```

#### Intraday: Trading (Every 5 minutes)
```bash
# Continuous loop
while true; do
  PYTHONPATH=. python -m qts.main \
    --symbols ETH BTC SOL XRP \
    --llm-provider openai \
    --execution-mode paper \
    --prompt prompts/canonical_intraday_prompt.md  # Uses current best
  sleep 300
done
```

#### Weekly: Tournament Validation
```bash
# Every Sunday, run tournament with new candidates
PYTHONPATH=. python -m qts.tournament \
  --variants current_best candidate_001 candidate_002 \
  --days 7

# Check if any candidate beats current_best
# If yes, update canonical_intraday_prompt.md
```

---

## 📊 Example: Complete Workflow

### Week 1: Discovery
```
Monday 06:00 - Research pipeline runs
├─> Analyzes ACE bullets from last week
├─> Notices: Long positions on low volume getting stopped out
├─> Proposes: "Only trade when volume > 24h avg * 1.5"
├─> Backtests: +2.3% improvement in Sharpe
└─> Generates: prompts/candidate_volume_filter.md

Monday-Sunday - Tournament validation
├─> tp_trail_1.0 (current): Sharpe 1.45, MDD -8%
└─> volume_filter (new): Sharpe 1.67, MDD -5% ✓ WINNER
```

### Week 2: Deployment
```
Monday 06:00 - Promote winner
├─> volume_filter passes promotion gate
├─> Copy to canonical_intraday_prompt.md
└─> Start using in live trading loop

Monday-Sunday - Continuous trading with new strategy
├─> Every 5 min: Trade with volume filter
├─> Market intelligence: Provides enhanced volume data
└─> ACE bullets: Log all decisions for next research cycle
```

### Week 3: Iteration
```
Monday 06:00 - Research pipeline runs again
├─> Analyzes bullets from volume_filter strategy
├─> Notices: Still losing on low ATR (choppy markets)
├─> Proposes: "Skip trades when ATR < 0.02 * price"
└─> Cycle continues...
```

---

## 🎯 What You're Using Right Now

**Current Setup**:
✅ **quant-trading-system** (QTS core) - You ran this!
✅ **tournament-runner** - You tested this!
❌ **research-execution-pipeline** - Not installed yet
❌ **market-intelligence** - Not installed yet

**What We Demonstrated**:
- QTS core with mock LLM
- Risk management rejections
- ACE bullet logging
- Tournament system (3-day, 2 variants)

**What's Missing**:
- Automated strategy discovery (research pipeline)
- Enhanced market data (market intelligence)
- Daily research loop
- Strategy evolution over time

---

## 🔧 Next Steps: Full System Integration

### 1. Keep Using QTS Core (What Works Now)
```bash
# You can already run:
PYTHONPATH=. python -m qts.main --symbols ETH BTC --llm-provider mock
PYTHONPATH=. python -m qts.tournament --days 7
```

### 2. Add Market Intelligence (Better Data)
```bash
# Install CCXT for real market data
pip install ccxt

# Update qts/main.py to use real data instead of mock
# Or install market-intelligence plugin for enhanced data
```

### 3. Add Research Pipeline (Strategy Evolution)
```bash
# Install DSPy for strategy discovery
pip install dspy-ai

# Set up daily research loop
# This generates new prompts automatically
```

### 4. Complete System (All 3 Working)
```
Research Pipeline → Tournament → QTS Execution → ACE Bullets → Research Pipeline
         ↑                                                              ↓
         └──────────────────── Continuous Learning ─────────────────────┘
```

---

## 💡 Key Insight

**Right Now**: You're using QTS core directly (Python scripts)
- Works great for testing and paper trading
- Manual prompt creation
- No automated strategy discovery

**With All 3 Plugins**: Complete autonomous system
- Automated strategy discovery via DSPy
- Continuous learning from ACE bullets
- Tournament validation of new strategies
- Best-in-class execution with risk management

**You Can Start Small**:
1. Use QTS core now (what we just did) ✅
2. Add real market data later (market-intelligence)
3. Add automated research when ready (research-execution-pipeline)

---

## 🎓 Summary

| Plugin | Purpose | Status | Next Step |
|--------|---------|--------|-----------|
| **quant-trading-system** | Execute trades with risk mgmt | ✅ Working | Use with OpenAI LLM |
| **tournament-runner** | Validate strategies | ✅ Working | Run 28-day tournament |
| **market-intelligence** | Enhanced market data | ❌ Not installed | Install for real data |
| **research-execution-pipeline** | Strategy discovery | ❌ Not installed | Install for automation |

**You have a working trading system now!** The other plugins enhance it with automation and better data.

Want to:
- Install market-intelligence for real CCXT data?
- Install research-pipeline for automated strategy discovery?
- Or keep using QTS core and manually iterate on strategies?
