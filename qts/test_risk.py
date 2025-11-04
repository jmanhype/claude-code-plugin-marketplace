"""
Comprehensive Tests for Risk Manager
======================================

Tests all risk management layers:
- Leverage caps (per-symbol and gross)
- Position sizing limits
- Stop-loss validation
- Daily loss limits
- Maximum drawdown
- Order rate limiting
- Circuit breaker
"""

import pytest
import time
from datetime import datetime, timedelta
from qts.risk import (
    RiskManager,
    RiskConfig,
    PortfolioState,
    RiskViolation,
    RiskCheckResult
)


class TestRiskConfig:
    """Test risk configuration loading and validation."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RiskConfig()
        assert config.leverage_btc_eth == 1.5
        assert config.leverage_other == 1.2
        assert config.leverage_gross == 1.5
        assert config.notional_per_symbol == 0.25
        assert config.notional_gross == 1.0
        assert config.daily_loss_limit == -0.05
        assert config.max_drawdown == -0.10

    def test_to_dict(self):
        """Test configuration serialization."""
        config = RiskConfig()
        data = config.to_dict()
        assert "leverage_btc_eth" in data
        assert "daily_loss_limit" in data
        assert data["max_drawdown"] == -0.10


class TestPortfolioState:
    """Test portfolio state tracking."""

    def test_initial_state(self):
        """Test initial portfolio state."""
        state = PortfolioState(equity=10000.0)
        assert state.equity == 10000.0
        assert state.daily_pnl == 0.0
        assert state.peak_equity == 0.0
        assert len(state.positions) == 0

    def test_drawdown_calculation(self):
        """Test drawdown calculation."""
        state = PortfolioState(equity=10000.0, peak_equity=10000.0)

        # No drawdown initially
        state.update_drawdown()
        assert state.current_drawdown == 0.0
        assert state.peak_equity == 10000.0

        # 5% drawdown
        state.equity = 9500.0
        state.update_drawdown()
        assert state.current_drawdown == -0.05

        # Recovery
        state.equity = 11000.0
        state.update_drawdown()
        assert state.peak_equity == 11000.0
        assert state.current_drawdown == 0.0

    def test_gross_notional_calculation(self):
        """Test gross notional calculation."""
        state = PortfolioState(equity=10000.0)
        state.positions = {
            "BTC": {"notional": 5000.0},
            "ETH": {"notional": 3000.0},
            "SOL": {"notional": -2000.0}
        }

        # Gross notional is sum of absolute values
        assert state.get_gross_notional() == 10000.0

    def test_gross_leverage_calculation(self):
        """Test gross leverage calculation."""
        state = PortfolioState(equity=10000.0)
        state.positions = {
            "BTC": {"notional": 5000.0},
            "ETH": {"notional": 3000.0}
        }

        assert state.get_gross_leverage() == 0.8  # 8000 / 10000


class TestRiskManager:
    """Test risk manager enforcement."""

    def test_valid_order_btc(self):
        """Test valid BTC order passes all checks."""
        config = RiskConfig()
        manager = RiskManager(config)

        result = manager.check_order(
            symbol="BTC",
            side="long",
            size=0.1,  # 10% of equity
            price=50000.0,
            leverage=1.3,
            stop_loss=0.015,
            atr=750.0
        )

        assert result.approved is True
        assert len(result.violations) == 0

    def test_leverage_per_symbol_btc_eth(self):
        """Test per-symbol leverage cap for BTC/ETH."""
        config = RiskConfig(leverage_btc_eth=1.5)
        manager = RiskManager(config)

        # Valid: 1.4x leverage
        result = manager.check_order(
            symbol="BTC",
            side="long",
            size=0.1,
            price=50000.0,
            leverage=1.4,
            stop_loss=0.01
        )
        assert result.approved is True

        # Invalid: 1.6x leverage
        result = manager.check_order(
            symbol="ETH",
            side="long",
            size=0.1,
            price=3000.0,
            leverage=1.6,
            stop_loss=0.01
        )
        assert result.approved is False
        assert RiskViolation.LEVERAGE_SYMBOL in result.violations

    def test_leverage_per_symbol_other(self):
        """Test per-symbol leverage cap for other coins."""
        config = RiskConfig(leverage_other=1.2)
        manager = RiskManager(config)

        # Valid: 1.1x leverage
        result = manager.check_order(
            symbol="SOL",
            side="long",
            size=0.1,
            price=100.0,
            leverage=1.1,
            stop_loss=0.01
        )
        assert result.approved is True

        # Invalid: 1.3x leverage
        result = manager.check_order(
            symbol="SOL",
            side="long",
            size=0.1,
            price=100.0,
            leverage=1.3,
            stop_loss=0.01
        )
        assert result.approved is False
        assert RiskViolation.LEVERAGE_SYMBOL in result.violations

    def test_gross_leverage_limit(self):
        """Test gross leverage limit across all positions."""
        config = RiskConfig(leverage_gross=1.5)
        state = PortfolioState(equity=10000.0)

        # Add existing position: 1.0x leverage
        state.positions = {"BTC": {"notional": 10000.0}}

        manager = RiskManager(config, state)

        # Try to add 0.6x more leverage (would exceed 1.5x total)
        result = manager.check_order(
            symbol="ETH",
            side="long",
            size=0.4,  # 40% of equity
            price=3000.0,
            leverage=1.5,  # 0.4 * 1.5 = 0.6x notional
            stop_loss=0.01
        )

        assert result.approved is False
        assert RiskViolation.LEVERAGE_GROSS in result.violations

    def test_notional_per_symbol_limit(self):
        """Test per-symbol notional limit."""
        config = RiskConfig(notional_per_symbol=0.25)  # 25% max
        manager = RiskManager(config)

        # Valid: 20% notional
        result = manager.check_order(
            symbol="BTC",
            side="long",
            size=0.2,
            price=50000.0,
            leverage=1.0,
            stop_loss=0.01
        )
        assert result.approved is True

        # Invalid: 30% notional
        result = manager.check_order(
            symbol="BTC",
            side="long",
            size=0.3,
            price=50000.0,
            leverage=1.0,
            stop_loss=0.01
        )
        assert result.approved is False
        assert RiskViolation.NOTIONAL_SYMBOL in result.violations

    def test_missing_stop_loss(self):
        """Test mandatory stop-loss requirement."""
        config = RiskConfig()
        manager = RiskManager(config)

        result = manager.check_order(
            symbol="BTC",
            side="long",
            size=0.1,
            price=50000.0,
            leverage=1.0,
            stop_loss=None  # Missing
        )

        assert result.approved is False
        assert RiskViolation.MISSING_STOP in result.violations

    def test_invalid_stop_loss_bounds(self):
        """Test stop-loss bounds validation."""
        config = RiskConfig(min_stop_pct=0.005, max_stop_pct=0.05)
        manager = RiskManager(config)

        # Too tight: 0.3%
        result = manager.check_order(
            symbol="BTC",
            side="long",
            size=0.1,
            price=50000.0,
            leverage=1.0,
            stop_loss=0.003
        )
        assert result.approved is False
        assert RiskViolation.INVALID_STOP in result.violations

        # Too wide: 6%
        result = manager.check_order(
            symbol="BTC",
            side="long",
            size=0.1,
            price=50000.0,
            leverage=1.0,
            stop_loss=0.06
        )
        assert result.approved is False
        assert RiskViolation.INVALID_STOP in result.violations

    def test_daily_loss_limit(self):
        """Test daily loss limit circuit breaker."""
        config = RiskConfig(daily_loss_limit=-0.05)  # -5%
        state = PortfolioState(equity=9500.0, daily_pnl=-500.0)  # -5% loss
        manager = RiskManager(config, state)

        result = manager.check_order(
            symbol="BTC",
            side="long",
            size=0.1,
            price=50000.0,
            leverage=1.0,
            stop_loss=0.01
        )

        assert result.approved is False
        assert RiskViolation.DAILY_LOSS in result.violations

    def test_max_drawdown_limit(self):
        """Test maximum drawdown circuit breaker."""
        config = RiskConfig(max_drawdown=-0.10)  # -10%
        state = PortfolioState(equity=9000.0, peak_equity=10000.0)  # -10% drawdown
        manager = RiskManager(config, state)

        result = manager.check_order(
            symbol="BTC",
            side="long",
            size=0.1,
            price=50000.0,
            leverage=1.0,
            stop_loss=0.01
        )

        assert result.approved is False
        assert RiskViolation.MAX_DRAWDOWN in result.violations

    def test_order_rate_limiting(self):
        """Test order rate limiting."""
        config = RiskConfig(max_orders_per_min=3)
        manager = RiskManager(config)

        # First 3 orders should pass rate check
        for i in range(3):
            result = manager.check_order(
                symbol="BTC",
                side="long",
                size=0.1,
                price=50000.0,
                leverage=1.0,
                stop_loss=0.01
            )
            manager.record_order("BTC", result.approved)
            # May have other violations, but not rate limit
            if not result.approved:
                assert RiskViolation.RATE_LIMIT not in result.violations

        # 4th order should trigger rate limit
        result = manager.check_order(
            symbol="BTC",
            side="long",
            size=0.1,
            price=50000.0,
            leverage=1.0,
            stop_loss=0.01
        )
        assert result.approved is False
        assert RiskViolation.RATE_LIMIT in result.violations

    def test_circuit_breaker(self):
        """Test circuit breaker activation."""
        config = RiskConfig(circuit_breaker_cooldown_min=60)
        manager = RiskManager(config)

        # Activate circuit breaker
        manager.trigger_circuit_breaker("Emergency halt")
        assert manager.state.circuit_breaker_until is not None

        # Orders should be rejected
        result = manager.check_order(
            symbol="BTC",
            side="long",
            size=0.1,
            price=50000.0,
            leverage=1.0,
            stop_loss=0.01
        )
        assert result.approved is False
        assert RiskViolation.CIRCUIT_BREAKER in result.violations

    def test_daily_loss_cooldown(self):
        """Test daily loss cooldown activation."""
        config = RiskConfig(daily_loss_cooldown_min=60)
        manager = RiskManager(config)

        # Activate cooldown
        manager.trigger_daily_loss_halt()
        assert manager.state.daily_loss_cooldown_until is not None

        # Orders should be rejected
        result = manager.check_order(
            symbol="BTC",
            side="long",
            size=0.1,
            price=50000.0,
            leverage=1.0,
            stop_loss=0.01
        )
        assert result.approved is False
        assert RiskViolation.DAILY_LOSS in result.violations

    def test_reset_daily(self):
        """Test daily counter reset."""
        config = RiskConfig()
        state = PortfolioState(equity=9500.0, daily_pnl=-500.0)
        manager = RiskManager(config, state)

        # Reset daily counters
        manager.reset_daily()

        assert manager.state.daily_pnl == 0.0
        assert manager.state.daily_loss_cooldown_until is None

    def test_multiple_violations(self):
        """Test multiple simultaneous violations."""
        config = RiskConfig(
            leverage_other=1.0,
            notional_per_symbol=0.1,
            min_stop_pct=0.01
        )
        manager = RiskManager(config)

        result = manager.check_order(
            symbol="SOL",
            side="long",
            size=0.3,  # Exceeds notional limit
            price=100.0,
            leverage=1.5,  # Exceeds leverage limit
            stop_loss=0.005,  # Below min stop
        )

        assert result.approved is False
        assert RiskViolation.LEVERAGE_SYMBOL in result.violations
        assert RiskViolation.NOTIONAL_SYMBOL in result.violations
        assert RiskViolation.INVALID_STOP in result.violations

    def test_serialization(self):
        """Test risk manager state serialization."""
        config = RiskConfig()
        state = PortfolioState(equity=10000.0, daily_pnl=-100.0)
        manager = RiskManager(config, state)

        data = manager.to_dict()

        assert "config" in data
        assert "state" in data
        assert data["state"]["equity"] == 10000.0
        assert data["state"]["daily_pnl"] == -100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
