"""
Quantitative Trading System (QTS)
===================================

Minimal, reliable intraday trading pipeline with:
- LLM-generated JSON trading decisions
- Multi-layer risk management with strict caps
- Paper trading by default (live requires approval)
- ACE bullet logging for every decision
- Tournament system for strategy validation

Safety first: All trades go through risk gates, circuit breakers, and daily loss limits.
"""

__version__ = "1.0.0"
