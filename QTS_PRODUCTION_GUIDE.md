# QTS Production Usage Guide

## 🎯 You've Successfully Set Up QTS v1.0.0!

### What You've Learned

1. ✅ **Pipeline Architecture**: Market data → LLM → Risk → Execution → Logging
2. ✅ **Risk Management**: Multi-layer safety (9+ violation types)
3. ✅ **ACE Bullet Logging**: Complete audit trail (state→action→result)
4. ✅ **Tournament System**: Multi-variant strategy comparison
5. ✅ **Safety Controls**: Risk rejections prevent bad trades BEFORE execution

---

## 📊 Tournament Results Explained

### Variant: tp_trail_1.0 (WINNER)
- **Total P&L**: +11.15% (15 trades over 3 days)
- **Hit Rate**: 60% (9 wins, 6 losses)
- **Sharpe Ratio**: 5.74 (excellent risk-adjusted returns)
- **Sortino Ratio**: 11.46 (great downside protection)
- **Max Drawdown**: -1.83% (very low)
- **Violations**: 0 (perfect compliance)

### Variant: tp_trail_1.5 (LOSER)
- **Total P&L**: -4.23% (losing variant)
- **Hit Rate**: 33.33% (5 wins, 10 losses)
- **Sharpe Ratio**: -2.30 (poor risk-adjusted returns)
- **Max Drawdown**: -7.02% (larger losses)
- **Violations**: 0 (compliant but unprofitable)

### Key Insight
- **Lower TP trail (1.0x ATR)** = Higher hit rate, smaller wins, better overall returns
- **Higher TP trail (1.5x ATR)** = Lower hit rate, targeting bigger wins but failing

---

## 🚀 Production Workflows

### 1. Single-Tick Testing (Quick Validation)
```bash
# Test with mock LLM (safe, no API costs)
PYTHONPATH=. python -m qts.main \
  --symbols ETH BTC \
  --llm-provider mock \
  --execution-mode paper

# Expected output:
# - Market data for each symbol
# - LLM decision (TRADE or NO_TRADE)
# - Risk check results (approved/rejected)
# - Execution results (if approved)
# - Bullet saved to logs/bullets/
```

### 2. Real LLM Integration (GPT-4 Decisions)
```bash
# Install OpenAI
pip install openai

# Set API key
export OPENAI_API_KEY=sk-your-key-here

# Run with GPT-4
PYTHONPATH=. python -m qts.main \
  --symbols ETH BTC SOL \
  --llm-provider openai \
  --execution-mode paper

# GPT-4 will:
# - Analyze market data
# - Make TRADE/NO_TRADE decisions
# - Provide detailed rationale
# - Follow risk management rules
```

### 3. Continuous Intraday Loop (Production)
```bash
# Create trading script
cat > run_intraday.sh << 'EOF'
#!/bin/bash
while true; do
  echo "=== Trading tick at $(date) ==="
  PYTHONPATH=. python -m qts.main \
    --symbols ETH BTC SOL XRP \
    --llm-provider openai \
    --execution-mode paper

  # Sleep 5 minutes (300 seconds)
  echo "Sleeping 5 minutes until next tick..."
  sleep 300
done
EOF

chmod +x run_intraday.sh
./run_intraday.sh

# This runs continuously, executing trades every 5 minutes
```

### 4. Full Tournament (4-Week Validation)
```bash
# Run 4-week tournament with 3 variants
PYTHONPATH=. python -m qts.tournament \
  --variants tp_trail_1.0 tp_trail_1.5 tp_trail_2.0 \
  --symbols ETH BTC SOL XRP DOGE BNB \
  --days 28

# Check if winning variant passes promotion gate
PYTHONPATH=. python -m qts.tournament \
  --variants tp_trail_1.0 tp_trail_1.5 tp_trail_2.0 \
  --days 28 \
  --check-gate tp_trail_1.0 \
  --gate-weeks 4

# Expected output:
# {
#   "pass": true/false,
#   "checks": {
#     "sharpe_gt_1.2": true,
#     "mdd_lt_10pct": true,
#     "hit_rate_gt_45pct": true,
#     "trades_per_week_gt_20": true,
#     "violations_zero": true
#   }
# }
```

### 5. Analyze Trading History
```python
# Python script to analyze bullets
from qts.bullets import BulletStore

store = BulletStore()

# Get all bullets
bullets = store.load_all()
print(f"Total trading decisions: {len(bullets)}")

# Count decisions
trades = [b for b in bullets if b.llm_decision['decision'] == 'TRADE']
no_trades = [b for b in bullets if b.llm_decision['decision'] == 'NO_TRADE']
print(f"TRADE decisions: {len(trades)}")
print(f"NO_TRADE decisions: {len(no_trades)}")

# Count rejections
rejected = store.query(tags=["rejected"])
print(f"Risk rejections: {len(rejected)}")

# Analyze violations
for bullet in rejected:
    violations = bullet.risk_check['violations']
    messages = bullet.risk_check['messages']
    print(f"\nSymbol: {bullet.symbol}")
    print(f"Violations: {violations}")
    print(f"Messages: {messages}")

# Get regime breakdown
stats = store.get_stats()
print(f"\nRegime statistics:")
print(f"Volatility: {stats['regimes']['volatility']}")
print(f"Trend: {stats['regimes']['trend']}")
```

---

## 🔧 Configuration Tweaks

### Adjust Risk Limits
Edit `config/qts.risk.json`:

```json
{
  "leverage_btc_eth": 1.2,     // Reduce BTC/ETH leverage to 1.2x
  "leverage_other": 1.0,        // Reduce altcoins to 1.0x (no leverage)
  "notional_per_symbol": 0.15,  // Reduce position size to 15% per symbol
  "daily_loss_limit": -0.03,    // Tighten daily loss limit to -3%
  "max_drawdown": -0.05         // Reduce max drawdown to -5%
}
```

### Customize Trading Prompt
Edit `prompts/canonical_intraday_prompt.md`:

```markdown
# Add your own rules
- Only trade during high volume hours (10:00-16:00 UTC)
- Avoid trading on weekends
- Require minimum volume of $100M
- Require price > MA20 for longs
- Etc.
```

---

## 📈 Promotion Gate Process

### Week 1: Scaffolding & Testing
```bash
# Run 7-day tournament to verify everything works
PYTHONPATH=. python -m qts.tournament --days 7
# ✓ Verify no errors
# ✓ Check violation counts
# ✓ Review leaderboard
```

### Weeks 2-6: Continuous Validation
```bash
# Run 28-day tournament
PYTHONPATH=. python -m qts.tournament --days 28

# Monitor daily:
# - Sharpe ratio trends
# - Drawdown levels
# - Violation counts
# - Hit rate stability
```

### Week 6: Gate Check
```bash
# Check promotion criteria
PYTHONPATH=. python -m qts.tournament \
  --days 28 \
  --check-gate <winning_variant> \
  --gate-weeks 4

# If pass == true:
# 1. Generate full report
# 2. Manual review
# 3. Risk team approval
# 4. Proceed to guarded live
```

### Post-Gate: Guarded Live Rollout
```bash
# Step 1: 1% size for 1 week
PYTHONPATH=. python -m qts.main \
  --symbols <winning_symbols> \
  --llm-provider openai \
  --execution-mode live  # Requires approval + enabled=True

# Step 2: Scale to 10% if successful
# Step 3: Scale to 50% if successful
# Step 4: Full deployment (100%)
```

---

## ⚠️ Safety Reminders

### 3-Layer Approval for Live Trading
1. **Code Flag**: `enabled=True` in executor init
2. **Plugin Permission**: `"trading": "live"` in plugin.json
3. **Manual Approval**: After 4-week gate passes

### Default to Paper
- All examples use `--execution-mode paper`
- No real money at risk
- Realistic slippage simulation

### Risk Manager Always Active
- Leverage caps enforced
- Position sizing enforced
- Stop-loss mandatory
- Daily loss limit with auto-flatten
- Max drawdown circuit breaker

### Complete Audit Trail
- Every decision logged as ACE bullet
- State→action→result
- Query rejected trades
- Analyze violation patterns

---

## 🎓 What You Can Do Now

✅ Run single-tick paper trades with mock or real LLM
✅ Set up continuous 5-minute trading loop
✅ Run multi-variant tournaments (7-day, 28-day)
✅ Check promotion gates
✅ Analyze trading history with ACE bullets
✅ Customize risk limits and trading prompts
✅ Understand multi-layer safety system

---

## 📚 Next Steps

1. **Experiment with LLMs**: Try OpenAI, DeepSeek, or custom prompts
2. **Run Longer Tournaments**: 28-day validation with multiple variants
3. **Analyze Bullet Data**: Build dashboards from ACE bullet logs
4. **Integrate Real Data**: Replace mock data with CCXT live prices
5. **Monitor Performance**: Track Sharpe, Sortino, MDD over time
6. **Iterate Strategy**: Refine canonical prompt based on results

---

**You're ready to run QTS in production (paper mode)!**

Questions? Check:
- `CHANGELOG.md` - Full v1.0.0 release notes
- `README.md` - QTS overview
- `plugins/tournament-runner/README.md` - Tournament guide
- `SECURITY.md` - Security model and approval flow

Happy trading! 📊🚀
