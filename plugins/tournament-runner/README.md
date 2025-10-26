# Tournament Runner Plugin

Multi-variant paper trading tournament orchestrator for objective strategy validation and promotion gating.

## Overview

The Tournament Runner provides a systematic approach to comparing trading strategy variants in a controlled paper trading environment. Run multiple variants simultaneously, track performance metrics, and use objective promotion gates to select winning strategies before live deployment.

## Features

### Multi-Variant Testing

- Run multiple strategy variants in parallel (e.g., `tp_trail_1.0x`, `tp_trail_1.5x`, `tp_trail_2.0x`)
- Each variant uses the same canonical prompt but different exit/take-profit parameters
- Isolates impact of specific parameter changes
- Fair comparison with identical market conditions

### Daily Leaderboards

Real-time performance tracking with key metrics:

- **Sharpe Ratio**: Risk-adjusted returns (annualized)
- **Sortino Ratio**: Downside-focused risk adjustment
- **Maximum Drawdown (MDD)**: Peak-to-trough decline
- **Hit Rate**: Percentage of winning trades
- **Average Hold Time**: Mean duration of positions (hours)
- **Violations**: Count of risk violations
- **Reject Rate**: Percentage of trades rejected by risk manager
- **Average Latency**: Mean execution latency (milliseconds)

### Promotion Gates

Objective criteria for live trading promotion (4-week validation):

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| Sharpe Ratio | > 1.2 | Strong risk-adjusted returns |
| Max Drawdown | < 10% | Capital preservation |
| Hit Rate | > 45% | Consistent edge |
| Trades/Week | > 20 | Sufficient sample size |
| Violations | = 0 | Perfect compliance |

All criteria must pass for promotion consideration.

### Deterministic Simulation

- **Reproducible Results**: Same variant produces identical outcomes across runs
- **Per-Variant RNG**: Each variant uses deterministic random seed based on name hash
- **A/B Testing**: Compare changes with confidence
- **Debugging**: Reproduce exact tournament scenarios

### JSON Output

Complete tournament results exported to JSON:

```json
{
  "timestamp": "2025-01-26T12:00:00Z",
  "variants": ["tp_trail_1.0", "tp_trail_1.5", "tp_trail_2.0"],
  "symbols": ["ETH", "SOL", "XRP", "BTC", "DOGE", "BNB"],
  "initial_equity": 10000.0,
  "results": {
    "tp_trail_1.5": {
      "name": "tp_trail_1.5",
      "total_trades": 35,
      "winning_trades": 18,
      "losing_trades": 17,
      "total_pnl": 234.56,
      "total_pnl_pct": 2.35,
      "sharpe": 1.34,
      "sortino": 1.89,
      "max_drawdown": -8.45,
      "hit_rate": 51.43,
      "avg_hold_hours": 4.2,
      "violations": 0,
      "reject_rate": 2.1,
      "avg_latency_ms": 145.6
    }
  }
}
```

## Installation

```bash
/plugin install tournament-runner
```

Requires: `quant-trading-system` (dependency)

## Usage

### Basic Tournament

Run a 7-day tournament with default variants:

```bash
PYTHONPATH=. python -m qts.tournament --days 7
```

Default variants: `tp_trail_1.0`, `tp_trail_1.5`, `tp_trail_2.0`

### Custom Variants

Specify your own variants:

```bash
PYTHONPATH=. python -m qts.tournament \
  --variants tp_trail_1.0 tp_trail_1.5 tp_trail_2.0 tp_trail_2.5 \
  --days 7
```

Variant naming convention: `tp_trail_<multiplier>` where multiplier is the take-profit trailing ATR multiplier.

### Custom Symbols

Test on specific trading pairs:

```bash
PYTHONPATH=. python -m qts.tournament \
  --symbols BTC ETH \
  --days 7
```

### Promotion Gate Check

Check if a variant meets promotion criteria (4-week data):

```bash
PYTHONPATH=. python -m qts.tournament \
  --variants tp_trail_1.0 tp_trail_1.5 tp_trail_2.0 \
  --days 28 \
  --check-gate tp_trail_1.5 \
  --gate-weeks 4
```

Output:

```json
{
  "variant": "tp_trail_1.5",
  "weeks": 4,
  "checks": {
    "sharpe_gt_1.2": true,
    "mdd_lt_10pct": true,
    "hit_rate_gt_45pct": true,
    "trades_per_week_gt_20": true,
    "violations_zero": true
  },
  "stats": { ... },
  "pass": true
}
```

## Tournament Workflow

### Week 1: Initial Testing

```bash
# Test 3 variants for 7 days
PYTHONPATH=. python -m qts.tournament --days 7
```

- Verify all variants complete successfully
- Check for violations or errors
- Review initial leaderboard ranking

### Weeks 2-6: Continuous Validation

```bash
# Run 28-day tournament (4 weeks)
PYTHONPATH=. python -m qts.tournament --days 28
```

- Collect sufficient trade samples (>80 trades)
- Monitor Sharpe, MDD, hit rate trends
- Identify top-performing variant

### Week 6: Promotion Gate

```bash
# Check if top variant passes gate
PYTHONPATH=. python -m qts.tournament \
  --days 28 \
  --check-gate tp_trail_1.5 \
  --gate-weeks 4
```

- If `pass: true`: Generate promotion report
- If `pass: false`: Iterate on strategy or extend testing

### Post-Gate: Guarded Rollout

1. **Manual Review**: Examine tournament logs, edge cases, violation history
2. **Approval**: Get sign-off from risk team
3. **1% Live**: Deploy winning variant at 1% of paper trading size
4. **Monitor**: Run for 1 week, watch for anomalies
5. **Scale**: 10% → 50% → 100% if successful

## Metrics Explained

### Sharpe Ratio

**Formula**: `(mean_return / std_dev) * sqrt(252)`

- Measures risk-adjusted returns (higher is better)
- Annualized by multiplying by sqrt(252) for daily returns
- Threshold: > 1.2 (strong performance)

### Sortino Ratio

**Formula**: `(mean_return / downside_std) * sqrt(252)`

- Focuses only on downside volatility
- Penalizes strategies with large losses more than Sharpe
- Calculation uses total number of returns in denominator (not just downside returns)

### Maximum Drawdown (MDD)

**Formula**: `(equity - peak_equity) / peak_equity`

- Largest peak-to-trough decline
- Measures capital preservation
- Threshold: < 10% (acceptable risk)

### Hit Rate

**Formula**: `winning_trades / total_trades`

- Percentage of profitable trades
- Does not account for magnitude (1% win = 10% win)
- Threshold: > 45% (consistent edge)

## Reproducibility Guarantees

### Deterministic RNG

Each variant uses a deterministic random seed:

```python
rng = random.Random(hash(variant.name) % (2**32))
```

**Guarantees**:
- Same variant name → same seed
- Same seed → identical random sequence
- Same sequence → identical trades, outcomes, metrics

**Benefits**:
- Compare changes with confidence (A/B testing)
- Reproduce exact scenarios for debugging
- Validate metric calculations

### Controlled Environment

- All variants run in same simulation loop
- Identical market conditions (symbols, dates, data)
- Fair comparison (no timing advantages)

## Configuration

Set environment variables in `.env` or shell:

```bash
# Tournament parameters
TOURNAMENT_VARIANTS=tp_trail_1.0,tp_trail_1.5,tp_trail_2.0
TOURNAMENT_DAYS=7
TOURNAMENT_SYMBOLS=ETH,SOL,XRP,BTC,DOGE,BNB

# Risk configuration (inherited from QTS)
# See config/qts.risk.json
```

## Output

Tournament results are saved to `logs/tournament/`:

```
logs/tournament/
├── tournament_20250126_120000.json  # Full results
├── tournament_20250126_130000.json
└── ...
```

Each file contains:
- Timestamp
- Variant configurations
- Complete performance metrics
- Promotion gate results (if checked)

## Known Limitations (v1.0.0)

### Simplified Simulation

**Current Implementation**:
- Uses mock simulation with random trades
- Trade outcomes based on heuristic probabilities
- Does NOT integrate with real trading pipeline or historical data

**Rationale**:
- v1 focuses on tournament infrastructure and promotion gates
- Real integration requires historical data feed, pipeline refactoring, time-series framework

**Future Enhancement**:
- v2.0.0 may include full pipeline integration with historical replay
- Realistic slippage models based on liquidity data
- Order book depth simulation

### Variant Limitations

- Currently only supports take-profit trailing ATR multiplier variations
- Other strategy parameters (entry logic, risk sizing) require code changes
- Future: Configuration-driven strategy variants

## Troubleshooting

### Zero Trades

**Symptoms**: Variant shows 0 trades after tournament run

**Causes**:
- Risk manager rejecting all orders (check violations)
- LLM provider errors (check logs)
- Market data fetch failures (mock should work)

**Solutions**:
- Review `config/qts.risk.json` for overly restrictive limits
- Check LLM provider credentials (if using OpenAI/DeepSeek)
- Verify PYTHONPATH includes project root

### Negative Sharpe/Sortino

**Symptoms**: Metrics show negative values

**Causes**:
- Mean returns are negative (losing strategy)
- Standard deviation calculation error

**Solutions**:
- Expected for poor-performing variants
- If all variants negative, check trade logic

### Division by Zero

**Symptoms**: `ZeroDivisionError` in metrics calculation

**Causes**:
- Zero trades (no returns to calculate)
- Zero standard deviation (all returns identical)

**Solutions**:
- v1.0.0 includes defensive guards (should not occur)
- If encountered, report as bug

## Examples

### Compare TP Multipliers

Test impact of take-profit trailing stop distance:

```bash
PYTHONPATH=. python -m qts.tournament \
  --variants tp_trail_1.0 tp_trail_1.5 tp_trail_2.0 tp_trail_2.5 tp_trail_3.0 \
  --days 14
```

**Hypothesis**: Higher TP multipliers reduce hit rate but increase avg win size.

### Symbol-Specific Testing

Test variant on specific asset class:

```bash
PYTHONPATH=. python -m qts.tournament \
  --variants tp_trail_1.5 \
  --symbols BTC \
  --days 28
```

### Full 4-Week Validation

Run complete promotion gate validation:

```bash
# Run 4-week tournament
PYTHONPATH=. python -m qts.tournament \
  --variants tp_trail_1.0 tp_trail_1.5 tp_trail_2.0 \
  --days 28

# Check gate for best variant (e.g., tp_trail_1.5)
PYTHONPATH=. python -m qts.tournament \
  --variants tp_trail_1.5 \
  --days 28 \
  --check-gate tp_trail_1.5 \
  --gate-weeks 4
```

## Contributing

Improvements welcome:

- Historical data integration
- More variant types (entry logic, risk sizing)
- Enhanced metrics (Calmar, Omega, win/loss ratio)
- Visualization dashboards
- Real-time tournament monitoring

Submit issues or PRs at: https://github.com/jmanhype/claude-code-plugin-marketplace

## License

MIT License - see main repository LICENSE file.

## Support

- **Issues**: https://github.com/jmanhype/claude-code-plugin-marketplace/issues
- **Docs**: https://github.com/jmanhype/claude-code-plugin-marketplace
- **QTS Core**: See `qts/tournament.py` for implementation details

---

**Built for systematic strategy validation and risk-controlled deployment.**
