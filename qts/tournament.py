"""
Tournament System
==================

Paper trading tournament with multiple strategy variants.

Features:
- Same prompt, different exit/TP variants
- Daily leaderboard with key metrics
- Promotion gate based on multi-week performance
- JSON output for analysis

Run with:
    PYTHONPATH=. python -m qts.tournament --variants tp_trail_1.0 tp_trail_1.5 --days 7
"""

import argparse
import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class VariantConfig:
    """Configuration for a tournament variant."""
    name: str
    tp_trail_atr_mult: float  # Take-profit trailing ATR multiplier
    description: str = ""


@dataclass
class Trade:
    """Individual trade record."""
    symbol: str
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    side: str
    size: float
    pnl: float = 0.0
    pnl_pct: float = 0.0
    hold_duration_hours: float = 0.0

    def close(self, exit_price: float, exit_time: datetime):
        """Close the trade."""
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.hold_duration_hours = (exit_time - self.entry_time).total_seconds() / 3600.0

        if self.side == "long":
            self.pnl_pct = (exit_price - self.entry_price) / self.entry_price
        else:  # short
            self.pnl_pct = (self.entry_price - exit_price) / self.entry_price

        self.pnl = self.pnl_pct * self.size


@dataclass
class VariantStats:
    """Performance statistics for a variant."""
    name: str
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    returns: List[float] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)

    # Metrics
    sharpe: float = 0.0
    sortino: float = 0.0
    max_drawdown: float = 0.0
    hit_rate: float = 0.0
    avg_hold_hours: float = 0.0
    violations: int = 0
    reject_rate: float = 0.0
    avg_latency_ms: float = 0.0

    def calculate_metrics(self):
        """Calculate derived metrics."""
        if self.total_trades == 0:
            return

        # Hit rate
        self.hit_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0.0

        # Sharpe ratio (assuming daily returns)
        if len(self.returns) > 1:
            mean_return = sum(self.returns) / len(self.returns)
            variance = sum((r - mean_return) ** 2 for r in self.returns) / (len(self.returns) - 1)
            std_dev = math.sqrt(variance) if variance > 0 else 1e-9
            self.sharpe = (mean_return / std_dev) * math.sqrt(252) if std_dev > 0 else 0.0

        # Sortino (downside deviation)
        downside_returns = [r for r in self.returns if r < 0]
        if len(downside_returns) > 1:
            mean_return = sum(self.returns) / len(self.returns)
            downside_variance = sum(r ** 2 for r in downside_returns) / len(downside_returns)
            downside_std = math.sqrt(downside_variance) if downside_variance > 0 else 1e-9
            self.sortino = (mean_return / downside_std) * math.sqrt(252) if downside_std > 0 else 0.0

        # Max drawdown
        if len(self.equity_curve) > 1:
            peak = self.equity_curve[0]
            max_dd = 0.0
            for equity in self.equity_curve:
                if equity > peak:
                    peak = equity
                dd = (equity - peak) / peak if peak > 0 else 0.0
                if dd < max_dd:
                    max_dd = dd
            self.max_drawdown = max_dd

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "total_pnl": round(self.total_pnl, 4),
            "total_pnl_pct": round(self.total_pnl_pct * 100, 2),
            "sharpe": round(self.sharpe, 2),
            "sortino": round(self.sortino, 2),
            "max_drawdown": round(self.max_drawdown * 100, 2),
            "hit_rate": round(self.hit_rate * 100, 2),
            "avg_hold_hours": round(self.avg_hold_hours, 2),
            "violations": self.violations,
            "reject_rate": round(self.reject_rate * 100, 2),
            "avg_latency_ms": round(self.avg_latency_ms, 2)
        }


class TournamentRunner:
    """
    Run paper trading tournament across multiple variants.

    Each variant uses the same canonical prompt but different exit strategies.
    """

    def __init__(
        self,
        variants: List[VariantConfig],
        symbols: List[str],
        initial_equity: float = 10000.0,
        output_dir: str = "logs/tournament"
    ):
        self.variants = variants
        self.symbols = symbols
        self.initial_equity = initial_equity
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.results: Dict[str, VariantStats] = {}

    def run_round(self, days: int = 7) -> Dict[str, VariantStats]:
        """
        Run one tournament round.

        Args:
            days: Number of days to simulate

        Returns:
            Results for each variant
        """
        print(f"\n{'=' * 70}")
        print(f"Tournament Round: {days} days, {len(self.variants)} variants, {len(self.symbols)} symbols")
        print(f"{'=' * 70}\n")

        # Initialize results
        for variant in self.variants:
            self.results[variant.name] = VariantStats(name=variant.name)

        # Run simulation for each variant
        for variant in self.variants:
            print(f"\nRunning variant: {variant.name} (TP trail: {variant.tp_trail_atr_mult}x ATR)")
            stats = self._simulate_variant(variant, days)
            stats.calculate_metrics()
            self.results[variant.name] = stats

            # Print summary
            print(f"  Trades: {stats.total_trades}, Win rate: {stats.hit_rate:.1%}, "
                  f"Sharpe: {stats.sharpe:.2f}, MDD: {stats.max_drawdown:.1%}")

        return self.results

    def _simulate_variant(self, variant: VariantConfig, days: int) -> VariantStats:
        """Simulate one variant over N days."""
        import random

        stats = VariantStats(name=variant.name)
        equity = self.initial_equity
        stats.equity_curve.append(equity)

        # Simple simulation: random trades with variant-specific TP
        trades_per_day = 5
        total_trades = days * trades_per_day

        for _ in range(total_trades):
            symbol = random.choice(self.symbols)
            side = "long" if random.random() < 0.6 else "short"

            # Simulate trade outcome based on variant TP multiplier
            # Higher TP = fewer wins but bigger wins
            win_prob = 0.5 - (variant.tp_trail_atr_mult - 1.0) * 0.1
            win_prob = max(0.3, min(0.7, win_prob))

            is_win = random.random() < win_prob
            if is_win:
                pnl_pct = random.uniform(0.01, 0.03) * variant.tp_trail_atr_mult
                stats.winning_trades += 1
            else:
                pnl_pct = random.uniform(-0.02, -0.01)
                stats.losing_trades += 1

            stats.total_trades += 1
            stats.returns.append(pnl_pct)

            # Update equity
            equity *= (1.0 + pnl_pct)
            stats.equity_curve.append(equity)

        stats.total_pnl = equity - self.initial_equity
        stats.total_pnl_pct = (equity - self.initial_equity) / self.initial_equity
        stats.avg_hold_hours = random.uniform(2.0, 6.0)
        stats.avg_latency_ms = random.uniform(100.0, 300.0)
        stats.reject_rate = random.uniform(0.0, 0.05)

        return stats

    def print_leaderboard(self):
        """Print leaderboard sorted by Sharpe ratio."""
        print(f"\n{'=' * 70}")
        print("LEADERBOARD (by Sharpe)")
        print(f"{'=' * 70}")

        sorted_variants = sorted(
            self.results.values(),
            key=lambda s: s.sharpe,
            reverse=True
        )

        print(f"{'Rank':<6}{'Variant':<20}{'Trades':<10}{'PnL%':<10}{'Sharpe':<10}{'MDD%':<10}{'Hit%':<10}")
        print("-" * 70)

        for rank, stats in enumerate(sorted_variants, 1):
            print(
                f"{rank:<6}"
                f"{stats.name:<20}"
                f"{stats.total_trades:<10}"
                f"{stats.total_pnl_pct*100:>8.2f}% "
                f"{stats.sharpe:>8.2f} "
                f"{stats.max_drawdown*100:>8.2f}% "
                f"{stats.hit_rate*100:>8.2f}%"
            )

    def check_promotion_gate(self, variant_name: str, weeks: int = 4) -> Dict[str, Any]:
        """
        Check if a variant meets promotion criteria.

        Criteria (from PRD):
        - Sharpe > 1.2
        - MDD < 10%
        - Hit rate > 45%
        - Trades/week > 20
        - Violations = 0

        Args:
            variant_name: Name of variant to check
            weeks: Number of weeks of data

        Returns:
            Gate check result with pass/fail and details
        """
        if variant_name not in self.results:
            return {"pass": False, "reason": "Variant not found"}

        stats = self.results[variant_name]
        trades_per_week = stats.total_trades / weeks if weeks > 0 else 0

        gate = {
            "variant": variant_name,
            "weeks": weeks,
            "checks": {
                "sharpe_gt_1.2": stats.sharpe > 1.2,
                "mdd_lt_10pct": stats.max_drawdown > -0.10,
                "hit_rate_gt_45pct": stats.hit_rate > 0.45,
                "trades_per_week_gt_20": trades_per_week > 20,
                "violations_zero": stats.violations == 0
            },
            "stats": stats.to_dict()
        }

        gate["pass"] = all(gate["checks"].values())
        return gate

    def save_results(self, filename: Optional[str] = None):
        """Save tournament results to JSON."""
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"tournament_{timestamp}.json"

        filepath = self.output_dir / filename

        output = {
            "timestamp": datetime.utcnow().isoformat(),
            "variants": [v.name for v in self.variants],
            "symbols": self.symbols,
            "initial_equity": self.initial_equity,
            "results": {name: stats.to_dict() for name, stats in self.results.items()}
        }

        with open(filepath, "w") as f:
            json.dump(output, f, indent=2)

        print(f"\nResults saved: {filepath}")
        return filepath


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="QTS Tournament - Paper Trading")
    parser.add_argument(
        "--variants",
        nargs="+",
        default=["tp_trail_1.0", "tp_trail_1.5", "tp_trail_2.0"],
        help="Variant names (format: tp_trail_<mult>)"
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["ETH", "SOL", "XRP", "BTC", "DOGE", "BNB"],
        help="Symbols to trade"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Days to simulate"
    )
    parser.add_argument(
        "--check-gate",
        help="Check promotion gate for variant"
    )
    parser.add_argument(
        "--gate-weeks",
        type=int,
        default=4,
        help="Weeks for promotion gate check"
    )

    args = parser.parse_args()

    # Parse variant configs
    variant_configs = []
    for name in args.variants:
        # Extract multiplier from name (e.g., tp_trail_1.5 -> 1.5)
        try:
            mult = float(name.split("_")[-1])
        except (ValueError, IndexError):
            mult = 1.0
            print(f"Warning: Could not parse multiplier from {name}, using 1.0")

        variant_configs.append(
            VariantConfig(
                name=name,
                tp_trail_atr_mult=mult,
                description=f"TP trailing stop at {mult}x ATR"
            )
        )

    # Run tournament
    tournament = TournamentRunner(
        variants=variant_configs,
        symbols=args.symbols
    )

    results = tournament.run_round(days=args.days)
    tournament.print_leaderboard()
    tournament.save_results()

    # Check promotion gate if requested
    if args.check_gate:
        gate_result = tournament.check_promotion_gate(args.check_gate, args.gate_weeks)
        print(f"\n{'=' * 70}")
        print(f"Promotion Gate Check: {args.check_gate}")
        print(f"{'=' * 70}")
        print(json.dumps(gate_result, indent=2))

        if gate_result["pass"]:
            print(f"\n✅ {args.check_gate} PASSED promotion gate!")
        else:
            failed_checks = [k for k, v in gate_result["checks"].items() if not v]
            print(f"\n❌ {args.check_gate} FAILED promotion gate:")
            print(f"   Failed checks: {', '.join(failed_checks)}")


if __name__ == "__main__":
    main()
