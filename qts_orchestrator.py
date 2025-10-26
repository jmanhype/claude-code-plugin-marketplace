#!/usr/bin/env python3
"""
QTS Autonomous Trading Orchestrator
====================================

Complete workflow integrating all 3 plugins:
1. Research-Execution-Pipeline: Strategy discovery via DSPy
2. Market-Intelligence: Real CCXT market data
3. Quant-Trading-System: Risk-managed execution

Workflow:
---------
1. Daily Research Loop (06:00)
   - Analyze ACE bullets from recent trades
   - Use DSPy to generate new strategy variants
   - Write new prompts to prompts/ directory

2. Tournament Validation
   - Test all strategy variants on recent data
   - Identify best performing strategy
   - Apply promotion gates

3. Live Execution
   - Execute best strategy with real market data
   - Log ACE bullets for next research cycle
   - Monitor performance

Usage:
------
# Full autonomous mode (daily research + tournament + execution)
python qts_orchestrator.py --mode autonomous --days 7

# Research only (generate new strategies)
python qts_orchestrator.py --mode research --days 7

# Tournament only (validate existing strategies)
python qts_orchestrator.py --mode tournament --days 3

# Execute only (run best strategy)
python qts_orchestrator.py --mode execute --symbols BTC ETH

# Test mode (use mock data)
python qts_orchestrator.py --mode test

Environment:
-----------
export OPENAI_API_KEY=your_key_here  # Required for research + LLM decisions
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure logs directory exists
Path("logs").mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class QTSOrchestrator:
    """
    Master orchestrator for autonomous trading system.

    Coordinates research, validation, and execution.
    """

    def __init__(
        self,
        use_real_data: bool = True,
        llm_provider: str = "openai",
        execution_mode: str = "paper"
    ):
        """
        Initialize orchestrator.

        Args:
            use_real_data: Use real CCXT market data
            llm_provider: LLM provider (openai, mock, deepseek)
            execution_mode: paper or live
        """
        self.use_real_data = use_real_data
        self.llm_provider = llm_provider
        self.execution_mode = execution_mode

        # Paths
        self.prompts_dir = Path("prompts")
        self.tournament_dir = Path("qts_tournament")
        self.logs_dir = Path("logs")

        # Ensure directories exist
        self.prompts_dir.mkdir(exist_ok=True)
        self.tournament_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

        logger.info(f"Orchestrator initialized: data={'REAL' if use_real_data else 'MOCK'}, "
                   f"llm={llm_provider}, mode={execution_mode}")

    def run_research_loop(self, days_lookback: int = 7) -> Dict[str, Any]:
        """
        Run research loop to discover new strategies.

        Returns:
            Research results with new strategy info
        """
        logger.info("=" * 80)
        logger.info("PHASE 1: RESEARCH LOOP (Strategy Discovery)")
        logger.info("=" * 80)

        try:
            from qts.research_loop import ResearchLoop

            loop = ResearchLoop(llm_model="gpt-4")
            result = loop.run_research_cycle(days_lookback=days_lookback)

            logger.info(f"✅ Research complete: {result['new_variant_name']}")
            logger.info(f"   Prompt: {result['new_prompt_path']}")
            logger.info(f"   Insights: {result['insights'][:150]}...")

            return result

        except Exception as e:
            logger.error(f"❌ Research loop failed: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def run_tournament(self, days: int = 3) -> Dict[str, Any]:
        """
        Run tournament to validate strategies.

        Returns:
            Tournament results with winner
        """
        logger.info("=" * 80)
        logger.info("PHASE 2: TOURNAMENT (Strategy Validation)")
        logger.info("=" * 80)

        try:
            cmd = [
                "python", "-m", "qts.tournament",
                "--days", str(days)
            ]

            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            logger.info("Tournament output:")
            logger.info(result.stdout)

            # Parse tournament results
            latest_result = self._get_latest_tournament_result()
            if latest_result:
                logger.info(f"✅ Tournament complete")
                logger.info(f"   Winner: {latest_result.get('winner', 'UNKNOWN')}")
                logger.info(f"   PnL: {latest_result.get('pnl', 0):.2f}")
                return latest_result
            else:
                logger.warning("Tournament completed but no results found")
                return {}

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Tournament failed: {e}")
            logger.error(e.stderr)
            return {"error": str(e)}

    def execute_best_strategy(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Execute the best strategy from tournament.

        Args:
            symbols: Symbols to trade

        Returns:
            Execution results
        """
        logger.info("=" * 80)
        logger.info("PHASE 3: EXECUTION (Live Trading)")
        logger.info("=" * 80)

        # Get best strategy from tournament
        tournament_result = self._get_latest_tournament_result()
        if tournament_result and 'winner' in tournament_result:
            best_variant = tournament_result['winner']
            logger.info(f"Using tournament winner: {best_variant}")
            prompt_path = self.prompts_dir / f"{best_variant}.md"
        else:
            logger.warning("No tournament winner found, using default")
            prompt_path = self.prompts_dir / "canonical_intraday_prompt.md"

        if not prompt_path.exists():
            logger.error(f"Prompt not found: {prompt_path}")
            return {"error": f"Prompt not found: {prompt_path}"}

        # Execute
        try:
            cmd = [
                "python", "-m", "qts.main",
                "--symbols", *symbols,
                "--llm-provider", self.llm_provider,
                "--execution-mode", self.execution_mode,
                "--prompt", str(prompt_path)
            ]

            if self.use_real_data:
                cmd.append("--use-market-intelligence")

            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            logger.info("Execution output:")
            logger.info(result.stdout)

            logger.info(f"✅ Execution complete")
            return {"success": True, "output": result.stdout}

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Execution failed: {e}")
            logger.error(e.stderr)
            return {"error": str(e), "stderr": e.stderr}

    def run_autonomous_mode(
        self,
        days_lookback: int = 7,
        tournament_days: int = 3,
        symbols: List[str] = ["BTC", "ETH"]
    ) -> Dict[str, Any]:
        """
        Run complete autonomous workflow.

        1. Research new strategies (DSPy)
        2. Validate via tournament
        3. Execute best strategy
        4. Repeat daily

        Returns:
            Complete workflow results
        """
        logger.info("=" * 80)
        logger.info("QTS AUTONOMOUS TRADING SYSTEM")
        logger.info("=" * 80)
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info(f"Market Data: {'REAL (CCXT)' if self.use_real_data else 'MOCK'}")
        logger.info(f"LLM Provider: {self.llm_provider}")
        logger.info(f"Execution Mode: {self.execution_mode}")
        logger.info("=" * 80)

        results = {
            'timestamp': datetime.now().isoformat(),
            'research': {},
            'tournament': {},
            'execution': {}
        }

        # Phase 1: Research
        if self.llm_provider != "mock":
            logger.info("\n🔬 Starting research phase...")
            results['research'] = self.run_research_loop(days_lookback)
        else:
            logger.info("\n⏭️  Skipping research (mock LLM)")

        # Phase 2: Tournament
        logger.info("\n🏆 Starting tournament phase...")
        results['tournament'] = self.run_tournament(tournament_days)

        # Phase 3: Execution
        logger.info("\n🚀 Starting execution phase...")
        results['execution'] = self.execute_best_strategy(symbols)

        # Save results
        self._save_workflow_results(results)

        logger.info("=" * 80)
        logger.info("AUTONOMOUS WORKFLOW COMPLETE")
        logger.info("=" * 80)

        return results

    def _get_latest_tournament_result(self) -> Optional[Dict[str, Any]]:
        """Get most recent tournament result."""
        if not self.tournament_dir.exists():
            return None

        # Find latest results.json
        result_files = sorted(self.tournament_dir.glob("**/results.json"))
        if not result_files:
            return None

        latest = result_files[-1]
        try:
            with open(latest) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load tournament results: {e}")
            return None

    def _save_workflow_results(self, results: Dict[str, Any]):
        """Save workflow results to log."""
        results_file = self.logs_dir / "workflow_results.jsonl"
        with open(results_file, 'a') as f:
            f.write(json.dumps(results) + "\n")
        logger.info(f"Results saved: {results_file}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="QTS Autonomous Trading Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--mode",
        choices=["autonomous", "research", "tournament", "execute", "test"],
        default="test",
        help="Orchestration mode"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Days of data to analyze (for research/tournament)"
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["BTC", "ETH"],
        help="Symbols to trade"
    )
    parser.add_argument(
        "--llm-provider",
        choices=["openai", "mock", "deepseek"],
        default="mock",
        help="LLM provider"
    )
    parser.add_argument(
        "--execution-mode",
        choices=["paper", "live"],
        default="paper",
        help="Execution mode"
    )
    parser.add_argument(
        "--use-mock-data",
        action="store_true",
        help="Use mock market data (default is real CCXT)"
    )

    args = parser.parse_args()

    # Check environment
    if args.llm_provider == "openai" and not os.getenv('OPENAI_API_KEY'):
        logger.error("OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    # Initialize orchestrator
    orchestrator = QTSOrchestrator(
        use_real_data=not args.use_mock_data,
        llm_provider=args.llm_provider,
        execution_mode=args.execution_mode
    )

    # Run requested mode
    if args.mode == "autonomous":
        orchestrator.run_autonomous_mode(
            days_lookback=args.days,
            tournament_days=min(args.days, 3),
            symbols=args.symbols
        )
    elif args.mode == "research":
        orchestrator.run_research_loop(days_lookback=args.days)
    elif args.mode == "tournament":
        orchestrator.run_tournament(days=args.days)
    elif args.mode == "execute":
        orchestrator.execute_best_strategy(symbols=args.symbols)
    elif args.mode == "test":
        logger.info("=" * 80)
        logger.info("TEST MODE: Quick validation of all components")
        logger.info("=" * 80)

        # Test with mock data and mock LLM
        test_orch = QTSOrchestrator(
            use_real_data=False,
            llm_provider="mock",
            execution_mode="paper"
        )

        logger.info("\n1️⃣ Testing execution...")
        exec_result = test_orch.execute_best_strategy(["BTC"])

        logger.info("\n2️⃣ Testing tournament...")
        tournament_result = test_orch.run_tournament(days=1)

        logger.info("\n=" * 80)
        logger.info("TEST COMPLETE")
        logger.info("=" * 80)
        logger.info("To run full autonomous mode:")
        logger.info("  export OPENAI_API_KEY=your_key")
        logger.info("  python qts_orchestrator.py --mode autonomous --llm-provider openai")


if __name__ == "__main__":
    main()
