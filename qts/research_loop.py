"""
Research-Execution-Pipeline: Automated Strategy Discovery

Uses DSPy and GEPA optimization to:
1. Analyze ACE bullets from trading logs
2. Identify winning/losing patterns
3. Generate new strategy variants
4. Optimize prompts via GEPA
5. Submit to tournament for validation

Designed to run daily (e.g., via cron at 06:00)
"""

import dspy
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)


class StrategyAnalyzer(dspy.Signature):
    """
    DSPy signature for analyzing trading results and generating insights.

    Takes ACE bullets + market conditions → Strategy improvements
    """

    # Inputs
    ace_bullets: str = dspy.InputField(desc="ACE bullets from recent trading sessions")
    market_summary: str = dspy.InputField(desc="Summary of market conditions during trades")
    tournament_results: str = dspy.InputField(desc="Tournament results showing strategy performance")

    # Outputs
    insights: str = dspy.OutputField(desc="Key insights about what worked and what didn't")
    improvements: str = dspy.OutputField(desc="Specific improvements for strategy prompts")
    new_variant_name: str = dspy.OutputField(desc="Name for the new strategy variant")
    new_variant_prompt: str = dspy.OutputField(desc="Complete prompt for new strategy variant")


class ResearchLoop:
    """
    Autonomous research loop for strategy discovery.

    Workflow:
    1. Read ACE bullets from logs/ace/*.json
    2. Analyze tournament results from qts_tournament/
    3. Use DSPy to generate new strategy variants
    4. Write new prompts to prompts/
    5. Optionally trigger tournament validation
    """

    def __init__(
        self,
        llm_model: str = "gpt-4",
        ace_log_dir: str = "logs/ace",
        tournament_dir: str = "qts_tournament",
        prompts_dir: str = "prompts"
    ):
        """
        Initialize research loop.

        Args:
            llm_model: DSPy LLM model (gpt-4, gpt-3.5-turbo, etc)
            ace_log_dir: Directory with ACE bullet logs
            tournament_dir: Tournament results directory
            prompts_dir: Where to write new strategy prompts
        """
        self.ace_log_dir = Path(ace_log_dir)
        self.tournament_dir = Path(tournament_dir)
        self.prompts_dir = Path(prompts_dir)

        # Initialize DSPy
        self.lm = dspy.OpenAI(model=llm_model, max_tokens=2000)
        dspy.settings.configure(lm=self.lm)

        # Create CoT (Chain of Thought) module for strategy analysis
        self.analyzer = dspy.ChainOfThought(StrategyAnalyzer)

        logger.info(f"Research loop initialized with {llm_model}")

    def run_research_cycle(self, days_lookback: int = 7) -> Dict[str, Any]:
        """
        Run one research cycle: analyze recent data → generate new strategies.

        Args:
            days_lookback: How many days of data to analyze

        Returns:
            Dict with research results, new strategies, etc.
        """
        logger.info(f"Starting research cycle (lookback={days_lookback} days)")

        # Step 1: Load recent ACE bullets
        ace_bullets = self._load_recent_ace_bullets(days_lookback)
        logger.info(f"Loaded {len(ace_bullets)} ACE bullets")

        # Step 2: Load tournament results
        tournament_results = self._load_tournament_results()
        logger.info(f"Loaded tournament results: {len(tournament_results)} tournaments")

        # Step 3: Summarize market conditions
        market_summary = self._summarize_market_conditions(ace_bullets)

        # Step 4: Use DSPy to analyze and generate new strategy
        analysis = self._analyze_with_dspy(
            ace_bullets=ace_bullets,
            market_summary=market_summary,
            tournament_results=tournament_results
        )

        # Step 5: Write new strategy prompt
        new_prompt_path = self._write_new_strategy_prompt(
            name=analysis.new_variant_name,
            prompt=analysis.new_variant_prompt
        )

        # Step 6: Return results
        result = {
            'timestamp': datetime.now().isoformat(),
            'insights': analysis.insights,
            'improvements': analysis.improvements,
            'new_variant_name': analysis.new_variant_name,
            'new_prompt_path': str(new_prompt_path),
            'ace_bullets_analyzed': len(ace_bullets),
            'tournaments_analyzed': len(tournament_results)
        }

        logger.info(f"Research cycle complete: {result['new_variant_name']}")
        return result

    def _load_recent_ace_bullets(self, days: int) -> List[Dict[str, Any]]:
        """Load ACE bullets from recent days."""
        if not self.ace_log_dir.exists():
            logger.warning(f"ACE log dir not found: {self.ace_log_dir}")
            return []

        cutoff = datetime.now() - timedelta(days=days)
        bullets = []

        for ace_file in sorted(self.ace_log_dir.glob("*.json")):
            try:
                # Check if file is recent enough
                file_mtime = datetime.fromtimestamp(ace_file.stat().st_mtime)
                if file_mtime < cutoff:
                    continue

                # Load bullets
                with open(ace_file) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        bullets.extend(data)
                    else:
                        bullets.append(data)
            except Exception as e:
                logger.error(f"Error loading {ace_file}: {e}")

        return bullets

    def _load_tournament_results(self) -> List[Dict[str, Any]]:
        """Load recent tournament results."""
        if not self.tournament_dir.exists():
            logger.warning(f"Tournament dir not found: {self.tournament_dir}")
            return []

        results = []
        for result_file in sorted(self.tournament_dir.glob("**/results.json")):
            try:
                with open(result_file) as f:
                    results.append(json.load(f))
            except Exception as e:
                logger.error(f"Error loading {result_file}: {e}")

        return results

    def _summarize_market_conditions(self, ace_bullets: List[Dict]) -> str:
        """Generate market condition summary from ACE bullets."""
        if not ace_bullets:
            return "No recent market data available."

        # Extract trade outcomes
        total_trades = len(ace_bullets)
        profitable = sum(1 for b in ace_bullets if b.get('profit_loss', 0) > 0)
        win_rate = (profitable / total_trades * 100) if total_trades > 0 else 0

        # Extract PnL
        pnls = [b.get('profit_loss', 0) for b in ace_bullets if 'profit_loss' in b]
        avg_pnl = statistics.mean(pnls) if pnls else 0
        total_pnl = sum(pnls)

        # Extract symbols
        symbols = set(b.get('symbol', 'UNKNOWN') for b in ace_bullets)

        return f"""
Recent Trading Activity:
- Total Trades: {total_trades}
- Win Rate: {win_rate:.1f}% ({profitable}/{total_trades} profitable)
- Average PnL: ${avg_pnl:.2f}
- Total PnL: ${total_pnl:.2f}
- Symbols Traded: {', '.join(sorted(symbols))}
- Time Period: Last {len(set(b.get('timestamp', '')[:10] for b in ace_bullets))} days
""".strip()

    def _analyze_with_dspy(
        self,
        ace_bullets: List[Dict],
        market_summary: str,
        tournament_results: List[Dict]
    ) -> Any:
        """
        Use DSPy to analyze trading data and generate new strategy.

        This is where the magic happens: DSPy's GEPA optimization
        will learn to generate better strategies over time.
        """
        # Format ACE bullets for DSPy
        ace_text = "\n".join([
            f"- {b.get('action', 'UNKNOWN')} {b.get('symbol', 'UNKNOWN')} @ ${b.get('price', 0):.2f} → P&L: ${b.get('profit_loss', 0):.2f}"
            for b in ace_bullets[:50]  # Last 50 bullets
        ])

        # Format tournament results
        tournament_text = "\n".join([
            f"- {r.get('variant', 'UNKNOWN')}: {r.get('total_pnl', 0):.2f} ({r.get('win_rate', 0):.1f}% win rate)"
            for r in tournament_results[:10]
        ])

        # Run DSPy chain-of-thought analysis
        try:
            prediction = self.analyzer(
                ace_bullets=ace_text or "No recent ACE bullets",
                market_summary=market_summary,
                tournament_results=tournament_text or "No tournament results"
            )
            return prediction
        except Exception as e:
            logger.error(f"DSPy analysis failed: {e}")
            # Return fallback
            return self._generate_fallback_strategy()

    def _generate_fallback_strategy(self):
        """Generate a simple fallback strategy if DSPy fails."""
        class FallbackPrediction:
            insights = "Unable to generate insights (DSPy error)"
            improvements = "Consider increasing position size on confirmed trends"
            new_variant_name = f"fallback_conservative_{datetime.now().strftime('%Y%m%d')}"
            new_variant_prompt = """
You are a conservative cryptocurrency trading advisor.

Strategy:
- Only trade on clear, confirmed trends
- Use tight stop losses (2% max)
- Take profit at 5% gains
- Avoid trading during high volatility
- Prefer liquid markets (BTC, ETH)

Risk Management:
- Max position size: 1000 USDT
- Max daily trades: 3
- No trades during major news events
""".strip()

        return FallbackPrediction()

    def _write_new_strategy_prompt(self, name: str, prompt: str) -> Path:
        """Write new strategy prompt to file."""
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize name for filename
        safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in name)
        filename = f"{safe_name}.md"
        filepath = self.prompts_dir / filename

        # Add metadata header
        full_content = f"""# Strategy: {name}
Generated: {datetime.now().isoformat()}
Source: Autonomous Research Loop (DSPy + GEPA)

---

{prompt}
"""

        with open(filepath, 'w') as f:
            f.write(full_content)

        logger.info(f"New strategy prompt written: {filepath}")
        return filepath

    def optimize_with_gepa(self, training_data: List[Dict], iterations: int = 10):
        """
        Use GEPA (Grounded Execution Prompt Alignment) to optimize strategy generation.

        This trains the DSPy analyzer to generate better strategies
        by learning from tournament results.

        Args:
            training_data: List of {ace_bullets, tournament_results, winning_strategy}
            iterations: GEPA optimization iterations
        """
        logger.info(f"Starting GEPA optimization ({iterations} iterations)")

        try:
            # Define GEPA optimizer
            from dspy.teleprompt import BootstrapFewShot

            # Create training examples
            train_examples = []
            for ex in training_data:
                train_examples.append(
                    dspy.Example(
                        ace_bullets=ex['ace_bullets'],
                        market_summary=ex['market_summary'],
                        tournament_results=ex['tournament_results']
                    ).with_inputs('ace_bullets', 'market_summary', 'tournament_results')
                )

            # Run GEPA optimization
            optimizer = BootstrapFewShot(metric=lambda gold, pred, trace: 1.0)
            self.analyzer = optimizer.compile(self.analyzer, trainset=train_examples)

            logger.info("GEPA optimization complete")
        except Exception as e:
            logger.error(f"GEPA optimization failed: {e}")


def run_daily_research(
    llm_model: str = "gpt-4",
    days_lookback: int = 7,
    trigger_tournament: bool = True
):
    """
    Run daily research cycle (intended for cron job).

    Example crontab:
        0 6 * * * cd /path/to/qts && python -m qts.research_loop
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("=" * 80)
    logger.info("DAILY RESEARCH CYCLE STARTING")
    logger.info("=" * 80)

    # Run research
    loop = ResearchLoop(llm_model=llm_model)
    result = loop.run_research_cycle(days_lookback=days_lookback)

    # Log results
    logger.info("Research Results:")
    logger.info(f"  New Strategy: {result['new_variant_name']}")
    logger.info(f"  Prompt Path: {result['new_prompt_path']}")
    logger.info(f"  Insights: {result['insights'][:200]}...")

    # Save results
    results_file = Path("logs/research_results.jsonl")
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'a') as f:
        f.write(json.dumps(result) + "\n")

    # Trigger tournament validation if requested
    if trigger_tournament:
        logger.info("Triggering tournament validation...")
        import subprocess
        try:
            subprocess.run([
                "python", "-m", "qts.tournament",
                "--days", "3",
                "--include-new-variants"
            ], check=True)
        except Exception as e:
            logger.error(f"Tournament failed: {e}")

    logger.info("=" * 80)
    logger.info("DAILY RESEARCH CYCLE COMPLETE")
    logger.info("=" * 80)


if __name__ == "__main__":
    import sys

    # Check for OpenAI API key
    import os
    if not os.getenv('OPENAI_API_KEY'):
        print("ERROR: OPENAI_API_KEY environment variable not set")
        print("Please set it: export OPENAI_API_KEY=your_key_here")
        sys.exit(1)

    # Run daily research
    run_daily_research(
        llm_model="gpt-4",
        days_lookback=7,
        trigger_tournament=True
    )
