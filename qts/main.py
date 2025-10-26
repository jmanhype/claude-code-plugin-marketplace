"""
Main Trading Loop
==================

Single-tick execution pipeline:
1. Fetch market data
2. LLM generates decision
3. Risk manager validates
4. Executor trades (paper/live)
5. ACE bullet logged

Run with:
    PYTHONPATH=. python -m qts.main --symbols ETH SOL XRP BTC DOGE BNB
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

from qts.llm_client import get_llm_client, DecisionType
from qts.risk import RiskManager, RiskConfig, PortfolioState
from qts.executor import get_executor, ExecutionResult
from qts.bullets import Bullet, BulletStore
from qts.market_intelligence import get_market_intelligence


def load_prompt(path: str = "prompts/canonical_intraday_prompt.md") -> str:
    """Load trading prompt from file."""
    prompt_path = Path(path)
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return prompt_path.read_text()


def fetch_market_data(symbol: str, use_market_intelligence: bool = False) -> Dict[str, Any]:
    """
    Fetch current market data for symbol.

    Args:
        symbol: Trading symbol (BTC, ETH, etc)
        use_market_intelligence: If True, use real CCXT data via MarketIntelligence

    Returns:
        Market data dict with price, volume, ATR, etc.
    """
    if use_market_intelligence:
        # Use real market data via CCXT
        try:
            mi = get_market_intelligence(exchange="binance", testnet=True)
            data = mi.get_market_data(symbol)

            # Convert to format expected by QTS
            return {
                "symbol": symbol,
                "price": data['current_price'],
                "volume": data['volume_24h'],
                "atr": data['current_price'] * data['volatility'],  # Approximate ATR from volatility
                "ma_20": data['current_price'],  # Would need historical data for real MA
                "timestamp": data['timestamp'],
                # Extra fields from market intelligence
                "bid": data['bid'],
                "ask": data['ask'],
                "spread_pct": data['spread_pct'],
                "volatility": data['volatility'],
                "order_book_imbalance": data['order_book_depth']['imbalance'],
                "market_intelligence_enabled": True
            }
        except Exception as e:
            print(f"Warning: Market Intelligence failed, falling back to mock: {e}")
            # Fall through to mock data

    # Mock data (original implementation)
    import random

    base_prices = {
        "BTC": 50000.0,
        "ETH": 3000.0,
        "SOL": 100.0,
        "XRP": 0.5,
        "DOGE": 0.1,
        "BNB": 400.0
    }

    price = base_prices.get(symbol, 1000.0)
    price *= random.uniform(0.98, 1.02)  # ±2% noise

    return {
        "symbol": symbol,
        "price": price,
        "volume": random.uniform(1e6, 1e8),
        "atr": price * random.uniform(0.01, 0.05),
        "ma_20": price * random.uniform(0.95, 1.05),
        "timestamp": "2025-01-01T00:00:00Z",
        "market_intelligence_enabled": False
    }


def run_tick(
    symbol: str,
    llm_client,
    risk_manager: RiskManager,
    executor,
    bullet_store: BulletStore,
    prompt: str,
    use_market_intelligence: bool = False
) -> Bullet:
    """
    Execute one trading tick.

    Args:
        symbol: Trading symbol
        llm_client: LLM client for decisions
        risk_manager: Risk manager
        executor: Trade executor
        bullet_store: ACE bullet store
        prompt: Trading strategy prompt
        use_market_intelligence: Use real CCXT data if True

    Returns:
        ACE bullet with full state→action→result
    """
    print(f"\n[{symbol}] Starting tick...")

    # 1. Fetch market data
    market_data = fetch_market_data(symbol, use_market_intelligence)
    mi_status = "🌐 REAL" if market_data.get('market_intelligence_enabled') else "🎲 MOCK"
    print(f"[{symbol}] Market ({mi_status}): {market_data['price']:.2f}, ATR: {market_data['atr']:.2f}")

    # 2. LLM decision
    decision = llm_client.get_decision(prompt, market_data)
    print(f"[{symbol}] LLM Decision: {decision.decision.value}")
    print(f"[{symbol}] Rationale: {decision.rationale}")

    # 3. Risk check
    risk_approved = True
    risk_result = None

    if decision.decision == DecisionType.TRADE and decision.actions:
        action = decision.actions[0]
        risk_result = risk_manager.check_order(
            symbol=action.get("symbol", symbol),
            side=action.get("type", "long"),
            size=action.get("size", 0.1),
            price=market_data["price"],
            leverage=decision.leverage,
            stop_loss=decision.stop_loss,
            atr=market_data["atr"]
        )

        risk_approved = risk_result.approved
        if not risk_approved:
            print(f"[{symbol}] RISK REJECTED: {', '.join(risk_result.messages)}")
        else:
            print(f"[{symbol}] Risk approved ✓")

    # Record order attempt
    risk_manager.record_order(symbol, risk_approved)

    # 4. Execute if approved
    execution_result = None
    if decision.decision == DecisionType.TRADE and risk_approved:
        exec_result = executor.execute(decision.actions)
        execution_result = {
            "success": exec_result.success,
            "fills": [f.to_dict() for f in exec_result.fills],
            "rejected": exec_result.rejected,
            "errors": exec_result.errors,
            "total_latency_ms": exec_result.total_latency_ms
        }

        if exec_result.success:
            print(f"[{symbol}] Executed: {len(exec_result.fills)} fills, latency {exec_result.total_latency_ms:.1f}ms")
        else:
            print(f"[{symbol}] Execution failed: {exec_result.errors}")

    # 5. Create ACE bullet
    bullet = Bullet.create(
        symbol=symbol,
        market_data=market_data,
        portfolio_state=risk_manager.to_dict()["state"],
        llm_decision={
            "decision": decision.decision.value,
            "actions": decision.actions,
            "leverage": decision.leverage,
            "stop_loss": decision.stop_loss,
            "rationale": decision.rationale
        },
        risk_check={
            "approved": risk_approved,
            "violations": [v.value for v in (risk_result.violations if risk_result else [])],
            "messages": risk_result.messages if risk_result else []
        },
        execution_result=execution_result,
        pnl=None,  # Would be calculated from fills
        violations=[v.value for v in (risk_result.violations if risk_result else [])]
    )

    # Add tags
    bullet.add_tag(f"symbol:{symbol}")
    bullet.add_tag(f"decision:{decision.decision.value}")
    if not risk_approved:
        bullet.add_tag("rejected")

    # Save bullet
    filepath = bullet_store.save(bullet)
    print(f"[{symbol}] Bullet saved: {filepath}")

    return bullet


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="QTS Trading System - Single Tick")
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["ETH", "SOL", "XRP", "BTC", "DOGE", "BNB"],
        help="Symbols to trade"
    )
    parser.add_argument(
        "--llm-provider",
        default="mock",
        choices=["mock", "openai", "deepseek"],
        help="LLM provider"
    )
    parser.add_argument(
        "--execution-mode",
        default="paper",
        choices=["paper", "live"],
        help="Execution mode"
    )
    parser.add_argument(
        "--risk-config",
        default="config/qts.risk.json",
        help="Path to risk config JSON"
    )
    parser.add_argument(
        "--prompt",
        default="prompts/canonical_intraday_prompt.md",
        help="Path to trading prompt"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run (no execution)"
    )
    parser.add_argument(
        "--use-market-intelligence",
        action="store_true",
        help="Use real CCXT market data (requires ccxt installed)"
    )

    args = parser.parse_args()

    # Load configuration
    try:
        if Path(args.risk_config).exists():
            risk_config = RiskConfig.from_file(args.risk_config)
        else:
            print(f"Warning: Risk config not found at {args.risk_config}, using defaults")
            risk_config = RiskConfig()

        prompt = load_prompt(args.prompt)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    # Initialize components
    llm_client = get_llm_client(args.llm_provider)
    risk_manager = RiskManager(risk_config)
    executor = get_executor(args.execution_mode)
    bullet_store = BulletStore()

    print("=" * 60)
    print("QTS Trading System")
    print("=" * 60)
    print(f"LLM Provider: {args.llm_provider}")
    print(f"Execution Mode: {args.execution_mode}")
    print(f"Symbols: {', '.join(args.symbols)}")
    print(f"Risk Config: {args.risk_config}")
    print(f"Market Intelligence: {'ENABLED (Real CCXT)' if args.use_market_intelligence else 'DISABLED (Mock Data)'}")
    print(f"Dry Run: {args.dry_run}")
    print("=" * 60)

    if args.dry_run:
        print("\n[DRY RUN] Would execute ticks but execution disabled")
        sys.exit(0)

    # Run ticks for each symbol
    bullets = []
    for symbol in args.symbols:
        try:
            bullet = run_tick(
                symbol=symbol,
                llm_client=llm_client,
                risk_manager=risk_manager,
                executor=executor,
                bullet_store=bullet_store,
                prompt=prompt,
                use_market_intelligence=args.use_market_intelligence
            )
            bullets.append(bullet)
        except Exception as e:
            print(f"[{symbol}] ERROR: {e}")
            import traceback
            traceback.print_exc()

    # Print summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total ticks: {len(bullets)}")
    print(f"Trades: {sum(1 for b in bullets if b.llm_decision['decision'] == 'TRADE')}")
    print(f"Rejected: {sum(1 for b in bullets if 'rejected' in b.tags)}")
    print(f"Executed: {sum(1 for b in bullets if isinstance(b.execution_result, dict) and b.execution_result.get('success'))}")

    stats = bullet_store.get_stats()
    print(f"\nBullet store: {stats['total']} total bullets")


if __name__ == "__main__":
    main()
