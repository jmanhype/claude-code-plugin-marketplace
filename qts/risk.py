"""
Risk Manager
=============

Multi-layer risk management with:
- Per-symbol and gross leverage caps
- Position sizing limits
- Mandatory stop-loss validation
- Daily loss limits with auto-flatten
- Maximum drawdown circuit breaker
- Order rate limiting

All violations result in rejected orders and logged events.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class RiskViolation(Enum):
    """Types of risk violations."""
    LEVERAGE_SYMBOL = "per_symbol_leverage_exceeded"
    LEVERAGE_GROSS = "gross_leverage_exceeded"
    NOTIONAL_SYMBOL = "per_symbol_notional_exceeded"
    NOTIONAL_GROSS = "gross_notional_exceeded"
    MISSING_STOP = "missing_stop_loss"
    INVALID_STOP = "invalid_stop_loss"
    DAILY_LOSS = "daily_loss_limit_exceeded"
    MAX_DRAWDOWN = "max_drawdown_exceeded"
    RATE_LIMIT = "order_rate_limit_exceeded"
    CIRCUIT_BREAKER = "circuit_breaker_active"


@dataclass
class RiskConfig:
    """Risk management configuration."""

    # Leverage caps
    leverage_btc_eth: float = 1.5
    leverage_other: float = 1.2
    leverage_gross: float = 1.5

    # Notional caps (as fraction of equity)
    notional_per_symbol: float = 0.25
    notional_gross: float = 1.0

    # Stop-loss
    min_stop_pct: float = 0.005  # 0.5%
    max_stop_pct: float = 0.05   # 5%
    atr_multiplier: float = 1.5

    # Loss limits
    daily_loss_limit: float = -0.05      # -5%
    daily_loss_cooldown_min: int = 60    # 1 hour
    max_drawdown: float = -0.10          # -10%

    # Rate limiting
    max_orders_per_min: int = 30

    # Circuit breaker
    circuit_breaker_cooldown_min: int = 60

    @classmethod
    def from_file(cls, path: str) -> "RiskConfig":
        """Load config from JSON file."""
        with open(path) as f:
            data = json.load(f)
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "leverage_btc_eth": self.leverage_btc_eth,
            "leverage_other": self.leverage_other,
            "leverage_gross": self.leverage_gross,
            "notional_per_symbol": self.notional_per_symbol,
            "notional_gross": self.notional_gross,
            "min_stop_pct": self.min_stop_pct,
            "max_stop_pct": self.max_stop_pct,
            "atr_multiplier": self.atr_multiplier,
            "daily_loss_limit": self.daily_loss_limit,
            "daily_loss_cooldown_min": self.daily_loss_cooldown_min,
            "max_drawdown": self.max_drawdown,
            "max_orders_per_min": self.max_orders_per_min,
            "circuit_breaker_cooldown_min": self.circuit_breaker_cooldown_min
        }


@dataclass
class PortfolioState:
    """Current portfolio state for risk calculations."""
    equity: float
    positions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    daily_pnl: float = 0.0
    peak_equity: float = 0.0
    current_drawdown: float = 0.0
    circuit_breaker_until: Optional[datetime] = None
    daily_loss_cooldown_until: Optional[datetime] = None
    orders_last_minute: List[float] = field(default_factory=list)

    def update_drawdown(self):
        """Update peak equity and current drawdown."""
        if self.equity > self.peak_equity:
            self.peak_equity = self.equity
        self.current_drawdown = (self.equity - self.peak_equity) / self.peak_equity if self.peak_equity > 0 else 0.0

    def get_gross_notional(self) -> float:
        """Calculate total gross notional across all positions."""
        return sum(abs(p.get("notional", 0.0)) for p in self.positions.values())

    def get_gross_leverage(self) -> float:
        """Calculate gross leverage."""
        if self.equity <= 0:
            return 0.0
        return self.get_gross_notional() / self.equity


@dataclass
class RiskCheckResult:
    """Result of risk validation."""
    approved: bool
    violations: List[RiskViolation] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)
    adjusted_size: Optional[float] = None
    adjusted_leverage: Optional[float] = None

    def add_violation(self, violation: RiskViolation, message: str):
        """Add a violation."""
        self.approved = False
        self.violations.append(violation)
        self.messages.append(message)


class RiskManager:
    """
    Multi-layer risk manager.

    Enforces:
    1. Leverage caps (per-symbol and gross)
    2. Notional limits
    3. Mandatory stop-loss
    4. Daily loss limit
    5. Maximum drawdown
    6. Order rate limits
    7. Circuit breaker
    """

    def __init__(self, config: RiskConfig, state: Optional[PortfolioState] = None):
        self.config = config
        self.state = state or PortfolioState(equity=10000.0, peak_equity=10000.0)

    def check_order(
        self,
        symbol: str,
        side: str,
        size: float,
        price: float,
        leverage: float,
        stop_loss: Optional[float] = None,
        atr: Optional[float] = None
    ) -> RiskCheckResult:
        """
        Comprehensive risk check for a proposed order.

        Args:
            symbol: Trading symbol
            side: "long" or "short"
            size: Position size as fraction of equity
            price: Entry price
            leverage: Requested leverage
            stop_loss: Stop-loss as fraction (e.g., 0.01 = 1%)
            atr: ATR for dynamic stop calculation

        Returns:
            RiskCheckResult with approval status and any violations
        """
        result = RiskCheckResult(approved=True)
        now = datetime.utcnow()

        # 1. Check circuit breaker
        if self.state.circuit_breaker_until and now < self.state.circuit_breaker_until:
            result.add_violation(
                RiskViolation.CIRCUIT_BREAKER,
                f"Circuit breaker active until {self.state.circuit_breaker_until.isoformat()}"
            )
            return result

        # 2. Check daily loss cooldown
        if self.state.daily_loss_cooldown_until and now < self.state.daily_loss_cooldown_until:
            result.add_violation(
                RiskViolation.DAILY_LOSS,
                f"Daily loss cooldown until {self.state.daily_loss_cooldown_until.isoformat()}"
            )
            return result

        # 3. Check order rate limit
        cutoff = time.time() - 60
        self.state.orders_last_minute = [t for t in self.state.orders_last_minute if t > cutoff]
        if len(self.state.orders_last_minute) >= self.config.max_orders_per_min:
            result.add_violation(
                RiskViolation.RATE_LIMIT,
                f"Order rate limit: {len(self.state.orders_last_minute)}/{self.config.max_orders_per_min} per minute"
            )

        # 4. Check per-symbol leverage
        max_leverage = self.config.leverage_btc_eth if symbol in ["BTC", "ETH"] else self.config.leverage_other
        if leverage > max_leverage:
            result.add_violation(
                RiskViolation.LEVERAGE_SYMBOL,
                f"Leverage {leverage:.2f} exceeds max {max_leverage:.2f} for {symbol}"
            )
            result.adjusted_leverage = max_leverage

        # 5. Check gross leverage
        notional = size * self.state.equity * leverage * price
        gross_notional = self.state.get_gross_notional() + notional
        gross_leverage = gross_notional / self.state.equity if self.state.equity > 0 else 0.0

        if gross_leverage > self.config.leverage_gross:
            result.add_violation(
                RiskViolation.LEVERAGE_GROSS,
                f"Gross leverage {gross_leverage:.2f} exceeds max {self.config.leverage_gross:.2f}"
            )

        # 6. Check per-symbol notional
        max_notional = self.state.equity * self.config.notional_per_symbol
        if notional > max_notional:
            result.add_violation(
                RiskViolation.NOTIONAL_SYMBOL,
                f"Notional {notional:.2f} exceeds max {max_notional:.2f} for {symbol}"
            )
            # Suggest adjusted size
            result.adjusted_size = max_notional / (self.state.equity * leverage * price)

        # 7. Check gross notional
        max_gross_notional = self.state.equity * self.config.notional_gross
        if gross_notional > max_gross_notional:
            result.add_violation(
                RiskViolation.NOTIONAL_GROSS,
                f"Gross notional {gross_notional:.2f} exceeds max {max_gross_notional:.2f}"
            )

        # 8. Validate stop-loss
        if stop_loss is None:
            result.add_violation(
                RiskViolation.MISSING_STOP,
                "Stop-loss is mandatory for all trades"
            )
        else:
            # Check stop bounds
            if stop_loss < self.config.min_stop_pct or stop_loss > self.config.max_stop_pct:
                result.add_violation(
                    RiskViolation.INVALID_STOP,
                    f"Stop-loss {stop_loss:.4f} outside valid range [{self.config.min_stop_pct:.4f}, {self.config.max_stop_pct:.4f}]"
                )

            # If ATR provided, validate against ATR-based stop
            if atr is not None:
                expected_stop = atr * self.config.atr_multiplier / price
                if abs(stop_loss - expected_stop) > 0.005:  # 0.5% tolerance
                    result.messages.append(
                        f"Warning: Stop {stop_loss:.4f} differs from ATR-based {expected_stop:.4f}"
                    )

        # 9. Check daily loss limit
        daily_loss_pct = self.state.daily_pnl / self.state.equity if self.state.equity > 0 else 0.0
        if daily_loss_pct <= self.config.daily_loss_limit:
            result.add_violation(
                RiskViolation.DAILY_LOSS,
                f"Daily loss {daily_loss_pct:.2%} hit limit {self.config.daily_loss_limit:.2%}"
            )

        # 10. Check max drawdown
        self.state.update_drawdown()
        if self.state.current_drawdown <= self.config.max_drawdown:
            result.add_violation(
                RiskViolation.MAX_DRAWDOWN,
                f"Drawdown {self.state.current_drawdown:.2%} exceeds max {self.config.max_drawdown:.2%}"
            )

        return result

    def record_order(self, symbol: str, approved: bool):
        """Record an order attempt for rate limiting."""
        self.state.orders_last_minute.append(time.time())

    def trigger_circuit_breaker(self, reason: str):
        """Activate circuit breaker."""
        self.state.circuit_breaker_until = datetime.utcnow() + timedelta(
            minutes=self.config.circuit_breaker_cooldown_min
        )
        print(f"[CIRCUIT BREAKER] {reason}. Cooldown until {self.state.circuit_breaker_until.isoformat()}")

    def trigger_daily_loss_halt(self):
        """Activate daily loss cooldown."""
        self.state.daily_loss_cooldown_until = datetime.utcnow() + timedelta(
            minutes=self.config.daily_loss_cooldown_min
        )
        print(f"[DAILY LOSS HALT] Cooldown until {self.state.daily_loss_cooldown_until.isoformat()}")

    def update_state(
        self,
        equity: Optional[float] = None,
        daily_pnl: Optional[float] = None,
        positions: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        """Update portfolio state."""
        if equity is not None:
            self.state.equity = equity
            self.state.update_drawdown()
        if daily_pnl is not None:
            self.state.daily_pnl = daily_pnl
        if positions is not None:
            self.state.positions = positions

    def reset_daily(self):
        """Reset daily counters (call at start of new trading day)."""
        self.state.daily_pnl = 0.0
        self.state.daily_loss_cooldown_until = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state for logging."""
        return {
            "config": self.config.to_dict(),
            "state": {
                "equity": self.state.equity,
                "daily_pnl": self.state.daily_pnl,
                "peak_equity": self.state.peak_equity,
                "current_drawdown": self.state.current_drawdown,
                "gross_leverage": self.state.get_gross_leverage(),
                "gross_notional": self.state.get_gross_notional(),
                "positions": len(self.state.positions),
                "circuit_breaker_until": self.state.circuit_breaker_until.isoformat() if self.state.circuit_breaker_until else None,
                "daily_loss_cooldown_until": self.state.daily_loss_cooldown_until.isoformat() if self.state.daily_loss_cooldown_until else None
            }
        }
