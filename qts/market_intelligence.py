"""
Market Intelligence Module - Real-time exchange data via CCXT

Integrates with market-intelligence plugin to provide:
- Real-time order book data
- Historical OHLCV
- Advanced technical indicators
- Multi-exchange aggregation
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)

# Try to import ccxt, but don't fail if it's not installed
try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    logger.warning("ccxt not installed - market intelligence will use mock data")


class MarketIntelligence:
    """
    Provides enhanced market data using CCXT.

    Features:
    - Order book depth analysis
    - Volume-weighted pricing
    - Cross-exchange arbitrage detection
    - Historical trend analysis
    """

    def __init__(self, exchange_name: str = "binance", testnet: bool = True):
        """
        Initialize market intelligence.

        Args:
            exchange_name: Exchange to connect to (binance, kraken, etc)
            testnet: Use testnet/sandbox if True
        """
        self.exchange_name = exchange_name
        self.exchange = self._init_exchange(exchange_name, testnet)
        logger.info(f"Market Intelligence initialized: {exchange_name} (testnet={testnet})")

    def _init_exchange(self, name: str, testnet: bool):
        """Initialize CCXT exchange."""
        if not CCXT_AVAILABLE:
            logger.warning("CCXT not available, returning None (will use mock data)")
            return None

        try:
            exchange_class = getattr(ccxt, name)
            exchange = exchange_class({
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })

            if testnet and hasattr(exchange, 'set_sandbox_mode'):
                exchange.set_sandbox_mode(True)
                logger.info(f"Sandbox mode enabled for {name}")

            return exchange
        except Exception as e:
            logger.error(f"Failed to initialize {name}: {e}")
            return None

    def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive market data for a symbol.

        Returns dict with:
        - current_price: Latest ticker price
        - bid/ask: Order book top of book
        - volume_24h: 24-hour volume
        - price_change_pct: 24h price change %
        - order_book_depth: Bid/ask depth analysis
        - volatility: Recent volatility measure
        """
        # If exchange not available, use fallback immediately
        if not self.exchange:
            return self._get_fallback_data(symbol)

        try:
            # Format symbol for CCXT (e.g., BTC → BTC/USDT)
            ccxt_symbol = self._format_symbol(symbol)

            # Fetch ticker
            ticker = self.exchange.fetch_ticker(ccxt_symbol)

            # Fetch order book
            order_book = self.exchange.fetch_order_book(ccxt_symbol, limit=20)

            # Fetch recent OHLCV for volatility
            ohlcv = self.exchange.fetch_ohlcv(ccxt_symbol, '1h', limit=24)

            # Calculate metrics
            volatility = self._calculate_volatility(ohlcv)
            depth_analysis = self._analyze_order_book_depth(order_book)

            return {
                'symbol': symbol,
                'current_price': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'spread_pct': ((ticker['ask'] - ticker['bid']) / ticker['last']) * 100,
                'volume_24h': ticker['quoteVolume'],
                'price_change_pct': ticker['percentage'],
                'high_24h': ticker['high'],
                'low_24h': ticker['low'],
                'volatility': volatility,
                'order_book_depth': depth_analysis,
                'timestamp': datetime.now().isoformat(),
                'exchange': self.exchange_name
            }

        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return self._get_fallback_data(symbol)

    def _format_symbol(self, symbol: str) -> str:
        """Convert symbol to CCXT format (e.g., BTC → BTC/USDT)."""
        if '/' in symbol:
            return symbol
        return f"{symbol}/USDT"

    def _calculate_volatility(self, ohlcv: List) -> float:
        """Calculate volatility from recent OHLCV data."""
        if not ohlcv or len(ohlcv) < 2:
            return 0.0

        # Calculate returns
        closes = [candle[4] for candle in ohlcv]  # Close prices
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]

        # Return standard deviation of returns
        return statistics.stdev(returns) if len(returns) > 1 else 0.0

    def _analyze_order_book_depth(self, order_book: Dict) -> Dict[str, float]:
        """
        Analyze order book depth.

        Returns bid/ask liquidity and imbalance metrics.
        """
        bids = order_book.get('bids', [])[:10]
        asks = order_book.get('asks', [])[:10]

        bid_liquidity = sum(price * volume for price, volume in bids) if bids else 0
        ask_liquidity = sum(price * volume for price, volume in asks) if asks else 0

        total_liquidity = bid_liquidity + ask_liquidity
        imbalance = (bid_liquidity - ask_liquidity) / total_liquidity if total_liquidity > 0 else 0

        return {
            'bid_liquidity': bid_liquidity,
            'ask_liquidity': ask_liquidity,
            'imbalance': imbalance,  # Positive = more buying pressure
            'bid_levels': len(bids),
            'ask_levels': len(asks)
        }

    def _get_fallback_data(self, symbol: str) -> Dict[str, Any]:
        """Return mock data if exchange is unavailable."""
        logger.warning(f"Using fallback mock data for {symbol}")
        return {
            'symbol': symbol,
            'current_price': 50000.0 if symbol == 'BTC' else 3000.0,
            'bid': 49990.0 if symbol == 'BTC' else 2995.0,
            'ask': 50010.0 if symbol == 'BTC' else 3005.0,
            'spread_pct': 0.04,
            'volume_24h': 1000000.0,
            'price_change_pct': 2.5,
            'high_24h': 51000.0 if symbol == 'BTC' else 3100.0,
            'low_24h': 49000.0 if symbol == 'BTC' else 2900.0,
            'volatility': 0.02,
            'order_book_depth': {
                'bid_liquidity': 500000.0,
                'ask_liquidity': 480000.0,
                'imbalance': 0.02,
                'bid_levels': 10,
                'ask_levels': 10
            },
            'timestamp': datetime.now().isoformat(),
            'exchange': 'mock',
            'is_mock': True
        }

    def get_multi_symbol_data(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get market data for multiple symbols."""
        return {symbol: self.get_market_data(symbol) for symbol in symbols}

    def format_for_llm_context(self, market_data: Dict[str, Any]) -> str:
        """
        Format market data for LLM prompt context.

        Returns human-readable market summary for strategy decisions.
        """
        depth = market_data['order_book_depth']

        return f"""
Market Data for {market_data['symbol']} ({market_data['exchange']}):
- Price: ${market_data['current_price']:.2f} (Bid: ${market_data['bid']:.2f}, Ask: ${market_data['ask']:.2f})
- 24h Change: {market_data['price_change_pct']:+.2f}% (High: ${market_data['high_24h']:.2f}, Low: ${market_data['low_24h']:.2f})
- Spread: {market_data['spread_pct']:.3f}%
- Volatility: {market_data['volatility']*100:.2f}%
- Order Book Imbalance: {depth['imbalance']:+.3f} ({"Bullish" if depth['imbalance'] > 0 else "Bearish"})
- Liquidity: Bids ${depth['bid_liquidity']:.0f} / Asks ${depth['ask_liquidity']:.0f}
- Volume 24h: ${market_data['volume_24h']:.0f}
""".strip()


# Global instance (lazy initialized)
_market_intelligence: Optional[MarketIntelligence] = None


def get_market_intelligence(exchange: str = "binance", testnet: bool = True) -> MarketIntelligence:
    """Get or create global MarketIntelligence instance."""
    global _market_intelligence
    if _market_intelligence is None:
        _market_intelligence = MarketIntelligence(exchange, testnet)
    return _market_intelligence
