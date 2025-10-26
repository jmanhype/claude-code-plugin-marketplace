"""
Trade Executor
==============

Executes trading decisions with two modes:
1. Paper trading (default): Simulated execution with realistic slippage
2. Live trading (disabled by default): Real exchange execution via CCXT

All executions are logged with timestamps, fill prices, and slippage.
"""

import time
import random
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class ExecutionMode(Enum):
    """Execution modes."""
    PAPER = "paper"
    LIVE = "live"


class OrderStatus(Enum):
    """Order status."""
    PENDING = "pending"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass
class Fill:
    """Trade fill details."""
    symbol: str
    side: str
    size: float
    entry_price: float
    fill_price: float
    slippage_bps: float
    timestamp: datetime
    latency_ms: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "size": self.size,
            "entry_price": self.entry_price,
            "fill_price": self.fill_price,
            "slippage_bps": self.slippage_bps,
            "timestamp": self.timestamp.isoformat(),
            "latency_ms": self.latency_ms
        }


@dataclass
class ExecutionResult:
    """Result of trade execution."""
    success: bool = False
    fills: List[Fill] = field(default_factory=list)
    rejected: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    total_latency_ms: float = 0.0

    def add_fill(self, fill: Fill):
        """Add a successful fill."""
        self.fills.append(fill)
        self.success = True

    def add_rejection(self, symbol: str, reason: str):
        """Add a rejected order."""
        self.rejected.append({"symbol": symbol, "reason": reason, "timestamp": datetime.utcnow().isoformat()})

    def add_error(self, message: str):
        """Add an error."""
        self.errors.append(message)
        self.success = False


class Executor:
    """Base class for trade executors."""

    def execute(self, actions: List[Dict[str, Any]]) -> ExecutionResult:
        """Execute a list of trading actions."""
        raise NotImplementedError


class PaperExecutor(Executor):
    """
    Paper trading executor with realistic simulation.

    Features:
    - Marketable-limit orders with configurable slippage
    - Random latency simulation (50-200ms)
    - Slippage based on order size and volatility
    """

    def __init__(
        self,
        slippage_tolerance_bps: float = 20.0,
        base_latency_ms: float = 50.0,
        max_latency_ms: float = 200.0
    ):
        """
        Initialize paper executor.

        Args:
            slippage_tolerance_bps: Maximum slippage in basis points
            base_latency_ms: Minimum simulated latency
            max_latency_ms: Maximum simulated latency
        """
        self.slippage_tolerance_bps = slippage_tolerance_bps
        self.base_latency_ms = base_latency_ms
        self.max_latency_ms = max_latency_ms
        self.rng = random.Random()

    def execute(self, actions: List[Dict[str, Any]]) -> ExecutionResult:
        """
        Execute actions in paper mode.

        Each action should have:
        - symbol: Trading pair
        - type: "long" or "short"
        - size: Position size
        - entry_price: Expected entry price
        """
        result = ExecutionResult()
        start = time.time()

        for action in actions:
            try:
                symbol = action["symbol"]
                side = action["type"]
                size = action["size"]
                entry_price = action["entry_price"]

                # Simulate latency
                latency = self.rng.uniform(self.base_latency_ms, self.max_latency_ms)
                time.sleep(latency / 1000.0)  # Convert to seconds

                # Simulate slippage (random within tolerance)
                slippage_bps = self.rng.uniform(-self.slippage_tolerance_bps, self.slippage_tolerance_bps)
                slippage_factor = 1.0 + (slippage_bps / 10000.0)

                # Adjust fill price based on side and slippage
                if side == "long":
                    fill_price = entry_price * slippage_factor
                else:  # short
                    fill_price = entry_price * (2.0 - slippage_factor)

                fill = Fill(
                    symbol=symbol,
                    side=side,
                    size=size,
                    entry_price=entry_price,
                    fill_price=fill_price,
                    slippage_bps=slippage_bps,
                    timestamp=datetime.utcnow(),
                    latency_ms=latency
                )
                result.add_fill(fill)

            except Exception as e:
                result.add_error(f"Failed to execute {action}: {str(e)}")

        result.total_latency_ms = (time.time() - start) * 1000.0
        return result


class LiveExecutor(Executor):
    """
    Live trading executor via CCXT.

    DISABLED BY DEFAULT. Requires explicit approval and API credentials.
    """

    def __init__(
        self,
        exchange: str = "binance",
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        testnet: bool = True,
        enabled: bool = False
    ):
        """
        Initialize live executor.

        Args:
            exchange: Exchange name (e.g., "binance", "bybit")
            api_key: API key
            api_secret: API secret
            testnet: Use testnet/sandbox (default: True)
            enabled: Explicit enable flag (default: False)
        """
        if not enabled:
            raise RuntimeError(
                "Live trading is DISABLED by default. Set enabled=True explicitly after approval."
            )

        self.exchange_name = exchange
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.ccxt_exchange = None

        # Initialize CCXT (lazy)
        self._init_exchange()

    def _init_exchange(self):
        """Initialize CCXT exchange connection."""
        try:
            import ccxt

            exchange_class = getattr(ccxt, self.exchange_name)
            config = {
                "apiKey": self.api_key,
                "secret": self.api_secret,
                "enableRateLimit": True
            }

            if self.testnet:
                config["options"] = {"defaultType": "future", "testnet": True}

            self.ccxt_exchange = exchange_class(config)
            print(f"[LiveExecutor] Connected to {self.exchange_name} (testnet={self.testnet})")

        except ImportError:
            raise RuntimeError("CCXT library not installed. Run: pip install ccxt")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize exchange: {str(e)}")

    def execute(self, actions: List[Dict[str, Any]]) -> ExecutionResult:
        """
        Execute actions on live exchange.

        WARNING: This trades with real money (or testnet funds).
        """
        result = ExecutionResult()
        start = time.time()

        if not self.ccxt_exchange:
            result.add_error("Exchange not initialized")
            return result

        for action in actions:
            try:
                symbol = action["symbol"]
                side = action["type"]  # "long" or "short"
                size = action["size"]
                entry_price = action.get("entry_price")

                # Map to CCXT order side
                ccxt_side = "buy" if side == "long" else "sell"

                # Place market order
                order_start = time.time()
                order = self.ccxt_exchange.create_market_order(
                    symbol=symbol,
                    side=ccxt_side,
                    amount=size
                )
                latency = (time.time() - order_start) * 1000.0

                # Parse fill
                fill_price = float(order.get("average", order.get("price", entry_price)))
                slippage_bps = 0.0
                if entry_price:
                    slippage_bps = ((fill_price - entry_price) / entry_price) * 10000.0

                fill = Fill(
                    symbol=symbol,
                    side=side,
                    size=size,
                    entry_price=entry_price or fill_price,
                    fill_price=fill_price,
                    slippage_bps=slippage_bps,
                    timestamp=datetime.utcnow(),
                    latency_ms=latency
                )
                result.add_fill(fill)

            except Exception as e:
                result.add_error(f"Live execution failed for {action}: {str(e)}")
                result.add_rejection(action.get("symbol", "UNKNOWN"), str(e))

        result.total_latency_ms = (time.time() - start) * 1000.0
        return result


def get_executor(mode: str = "paper", **kwargs) -> Executor:
    """
    Factory function to create executor.

    Args:
        mode: "paper" or "live"
        **kwargs: Mode-specific arguments

    Returns:
        Executor instance
    """
    if mode == "paper":
        return PaperExecutor(**kwargs)
    elif mode == "live":
        # Live mode requires explicit approval
        if not kwargs.get("enabled", False):
            raise RuntimeError(
                "Live trading requires explicit approval. "
                "Pass enabled=True after manual approval and risk review."
            )
        return LiveExecutor(**kwargs)
    else:
        raise ValueError(f"Unknown execution mode: {mode}. Choose 'paper' or 'live'.")
