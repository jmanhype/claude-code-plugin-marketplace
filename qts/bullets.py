"""
ACE Bullet Logger
==================

Creates ACE (Agentic Context Engineering) bullets for every trading decision.

Each bullet contains:
- State: Market conditions, portfolio state, regime tags
- Action: LLM decision, risk check, execution result
- Result: Fill prices, P&L, violations
- Edges: Relationships to other bullets (led_to, confirmed_by, invalidated_by, same_regime_as)

Bullets are stored as JSON files and can be retrieved for analysis and learning.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class Regime:
    """Market regime classification."""
    volatility: str  # "low", "medium", "high"
    trend: str       # "up", "down", "sideways"
    liquidity: str   # "high", "medium", "low"

    @classmethod
    def from_market_data(cls, data: Dict[str, Any]) -> "Regime":
        """
        Infer regime from market data.

        Simple heuristics:
        - Volatility: based on ATR percentile
        - Trend: based on price vs moving averages
        - Liquidity: based on volume
        """
        atr = data.get("atr", 0.0)
        price = data.get("price", 0.0)
        ma_20 = data.get("ma_20", price)
        volume = data.get("volume", 0.0)

        # Simple volatility classification
        if atr / price < 0.02:
            volatility = "low"
        elif atr / price < 0.05:
            volatility = "medium"
        else:
            volatility = "high"

        # Trend classification
        if price > ma_20 * 1.02:
            trend = "up"
        elif price < ma_20 * 0.98:
            trend = "down"
        else:
            trend = "sideways"

        # Liquidity (placeholder logic)
        liquidity = "medium"  # Would use actual volume percentiles in production

        return cls(volatility=volatility, trend=trend, liquidity=liquidity)

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "volatility": self.volatility,
            "trend": self.trend,
            "liquidity": self.liquidity
        }


@dataclass
class Edge:
    """Relationship edge to another bullet."""
    type: str  # "led_to", "confirmed_by", "invalidated_by", "same_regime_as"
    target_id: str
    weight: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "target_id": self.target_id,
            "weight": self.weight
        }


@dataclass
class Bullet:
    """
    ACE bullet: state → action → result.

    Captures the full context of a trading decision for later retrieval and analysis.
    """
    id: str
    timestamp: datetime
    symbol: str

    # State
    market_data: Dict[str, Any]
    portfolio_state: Dict[str, Any]
    regime: Regime

    # Action
    llm_decision: Dict[str, Any]
    risk_check: Dict[str, Any]

    # Result
    execution_result: Optional[Dict[str, Any]] = None
    pnl: Optional[float] = None
    violations: List[str] = field(default_factory=list)

    # Edges
    edges: List[Edge] = field(default_factory=list)

    # Metadata
    tags: List[str] = field(default_factory=list)
    notes: str = ""

    @classmethod
    def create(
        cls,
        symbol: str,
        market_data: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        llm_decision: Dict[str, Any],
        risk_check: Dict[str, Any],
        execution_result: Optional[Dict[str, Any]] = None,
        pnl: Optional[float] = None,
        violations: Optional[List[str]] = None
    ) -> "Bullet":
        """
        Create a new bullet.

        Automatically generates ID and infers regime from market data.
        """
        timestamp = datetime.utcnow()
        regime = Regime.from_market_data(market_data)

        # Generate deterministic ID from content
        content = f"{timestamp.isoformat()}:{symbol}:{json.dumps(llm_decision, sort_keys=True)}"
        bullet_id = hashlib.sha256(content.encode()).hexdigest()[:16]

        return cls(
            id=bullet_id,
            timestamp=timestamp,
            symbol=symbol,
            market_data=market_data,
            portfolio_state=portfolio_state,
            regime=regime,
            llm_decision=llm_decision,
            risk_check=risk_check,
            execution_result=execution_result,
            pnl=pnl,
            violations=violations or [],
            edges=[],
            tags=[]
        )

    def add_edge(self, edge_type: str, target_id: str, weight: float = 1.0):
        """Add a relationship edge."""
        self.edges.append(Edge(type=edge_type, target_id=target_id, weight=weight))

    def add_tag(self, tag: str):
        """Add a tag."""
        if tag not in self.tags:
            self.tags.append(tag)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "state": {
                "market_data": self.market_data,
                "portfolio_state": self.portfolio_state,
                "regime": self.regime.to_dict()
            },
            "action": {
                "llm_decision": self.llm_decision,
                "risk_check": self.risk_check
            },
            "result": {
                "execution_result": self.execution_result,
                "pnl": self.pnl,
                "violations": self.violations
            },
            "edges": [e.to_dict() for e in self.edges],
            "tags": self.tags,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Bullet":
        """Load from dictionary."""
        regime = Regime(**data["state"]["regime"])
        edges = [Edge(**e) for e in data.get("edges", [])]

        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            symbol=data["symbol"],
            market_data=data["state"]["market_data"],
            portfolio_state=data["state"]["portfolio_state"],
            regime=regime,
            llm_decision=data["action"]["llm_decision"],
            risk_check=data["action"]["risk_check"],
            execution_result=data["result"].get("execution_result"),
            pnl=data["result"].get("pnl"),
            violations=data["result"].get("violations", []),
            edges=edges,
            tags=data.get("tags", []),
            notes=data.get("notes", "")
        )


class BulletStore:
    """
    Store and retrieve ACE bullets.

    Bullets are saved as individual JSON files in logs/bullets/
    with filenames: bullet-YYYY-MM-DD-NNN.json
    """

    def __init__(self, storage_path: str = "logs/bullets"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def save(self, bullet: Bullet) -> Path:
        """
        Save a bullet to disk.

        Returns:
            Path to saved file
        """
        # Generate filename with date and sequence
        date_str = bullet.timestamp.strftime("%Y-%m-%d")
        existing = list(self.storage_path.glob(f"bullet-{date_str}-*.json"))
        seq = len(existing) + 1

        filename = f"bullet-{date_str}-{seq:03d}.json"
        filepath = self.storage_path / filename

        with open(filepath, "w") as f:
            json.dump(bullet.to_dict(), f, indent=2)

        return filepath

    def load(self, bullet_id: str) -> Optional[Bullet]:
        """Load a bullet by ID."""
        for filepath in self.storage_path.glob("bullet-*.json"):
            with open(filepath) as f:
                data = json.load(f)
                if data["id"] == bullet_id:
                    return Bullet.from_dict(data)
        return None

    def load_all(self, limit: Optional[int] = None) -> List[Bullet]:
        """
        Load all bullets, sorted by timestamp (newest first).

        Args:
            limit: Maximum number of bullets to load

        Returns:
            List of bullets
        """
        bullets = []
        files = sorted(self.storage_path.glob("bullet-*.json"), reverse=True)

        for filepath in files[:limit] if limit else files:
            with open(filepath) as f:
                data = json.load(f)
                bullets.append(Bullet.from_dict(data))

        return bullets

    def query(
        self,
        symbol: Optional[str] = None,
        regime: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[Bullet]:
        """
        Query bullets with filters.

        Args:
            symbol: Filter by symbol
            regime: Filter by regime (e.g., {"volatility": "high"})
            tags: Filter by tags
            limit: Maximum results

        Returns:
            Filtered bullets
        """
        bullets = self.load_all()
        results = []

        for bullet in bullets:
            # Filter by symbol
            if symbol and bullet.symbol != symbol:
                continue

            # Filter by regime
            if regime:
                match = all(
                    getattr(bullet.regime, k, None) == v
                    for k, v in regime.items()
                )
                if not match:
                    continue

            # Filter by tags
            if tags and not any(tag in bullet.tags for tag in tags):
                continue

            results.append(bullet)

            if limit and len(results) >= limit:
                break

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored bullets."""
        bullets = self.load_all()

        if not bullets:
            return {"total": 0}

        return {
            "total": len(bullets),
            "symbols": len(set(b.symbol for b in bullets)),
            "date_range": {
                "start": min(b.timestamp for b in bullets).isoformat(),
                "end": max(b.timestamp for b in bullets).isoformat()
            },
            "regimes": {
                "volatility": {
                    "low": sum(1 for b in bullets if b.regime.volatility == "low"),
                    "medium": sum(1 for b in bullets if b.regime.volatility == "medium"),
                    "high": sum(1 for b in bullets if b.regime.volatility == "high")
                },
                "trend": {
                    "up": sum(1 for b in bullets if b.regime.trend == "up"),
                    "down": sum(1 for b in bullets if b.regime.trend == "down"),
                    "sideways": sum(1 for b in bullets if b.regime.trend == "sideways")
                }
            },
            "violations": sum(len(b.violations) for b in bullets)
        }
