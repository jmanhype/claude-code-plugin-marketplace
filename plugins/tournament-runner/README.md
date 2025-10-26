# Tournament Runner Plugin

Paper trading tournament orchestrator for systematic strategy testing and validation.

## Overview

Runs multi-variant paper trading tournaments to objectively compare strategy variants before live deployment. Uses fixed prompts with different exit/TP parameters to isolate performance differences.

## Features

- **Multi-variant testing**: Same prompt, different exit strategies (e.g., TP trail 1.0x vs 1.5x ATR)
- **Daily leaderboards**: Track PnL, Sharpe, Sortino, MDD, hit rate, violations
- **Objective promotion gates**: 4-week criteria (Sharpe >1.2, MDD <10%, hit rate >45%, trades/week >20)
- **Paper-only**: All trading is simulated; no real capital at risk
- **JSON output**: Results saved for analysis and dashboards

## Usage

### Run Tournament

```bash
PYTHONPATH=. python -m qts.tournament \
  --variants tp_trail_1.0 tp_trail_1.5 tp_trail_2.0 \
  --symbols ETH SOL XRP BTC DOGE BNB \
  --days 7
```

### Check Promotion Gate

```bash
PYTHONPATH=. python -m qts.tournament \
  --check-gate tp_trail_1.5 \
  --gate-weeks 4
```

## Promotion Criteria

A variant passes the promotion gate if ALL criteria are met over 4 consecutive weeks:

| Metric | Requirement |
|--------|-------------|
| Sharpe Ratio | > 1.2 |
| Max Drawdown | < 10% |
| Hit Rate | > 45% |
| Trades/Week | > 20 |
| Violations | = 0 |

## Tournament Variants

Variants use the same `canonical_intraday_prompt.md` but differ in exit parameters:

- `tp_trail_1.0`: Take-profit trailing stop at 1.0× ATR
- `tp_trail_1.5`: Take-profit trailing stop at 1.5× ATR
- `tp_trail_2.0`: Take-profit trailing stop at 2.0× ATR

Higher TP multipliers = fewer wins but larger wins (risk/reward tradeoff).

## Output

Results are saved to `logs/tournament/tournament_<timestamp>.json`:

```json
{
  "timestamp": "2025-01-15T12:00:00Z",
  "variants": ["tp_trail_1.0", "tp_trail_1.5", "tp_trail_2.0"],
  "symbols": ["ETH", "SOL", "XRP", "BTC", "DOGE", "BNB"],
  "results": {
    "tp_trail_1.5": {
      "total_trades": 150,
      "total_pnl_pct": 12.5,
      "sharpe": 1.45,
      "sortino": 1.82,
      "max_drawdown": -7.2,
      "hit_rate": 48.5,
      "violations": 0
    }
  }
}
```

## Integration with QTS

The tournament runner uses the core QTS modules:
- `qts.llm_client` for LLM decisions
- `qts.risk` for risk management
- `qts.executor` for paper trading
- `qts.bullets` for ACE logging

## Permissions

- **filesystem**: true (read/write tournament results)
- **network**: false (no external calls)
- **exec**: true (runs Python subprocesses)
- **env**: true (reads tournament config from env)
- **trading**: paper (paper trading only)

## Dependencies

- **quant-trading-system**: Core trading infrastructure
- Python 3.11+
- See `requirements.txt` for Python packages

## Safety

- **Paper trading only**: No live trading allowed
- **No network access**: Runs in isolation
- **No secrets required**: Uses mock LLM by default
- **Read-only on failure**: All violations logged, no retries

## Next Steps

After a variant passes the 4-week gate:
1. Generate promotion report with full stats
2. Manual review and approval
3. Upgrade to guarded live mode (small size, strict limits)
4. Monitor for 2 more weeks before full deployment

## References

- [PRD: Intraday LLM Trading Pipeline](../../README.md)
- [QTS Risk Config](../../config/qts.risk.json)
- [Canonical Trading Prompt](../../prompts/canonical_intraday_prompt.md)
