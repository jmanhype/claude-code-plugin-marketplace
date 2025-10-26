"""
LLM Client for Trading Decisions
==================================

Provides interfaces to LLM providers (OpenAI, DeepSeek) and a local heuristic mock.
All LLMs must return JSON decisions matching the canonical prompt schema.
"""

import json
import os
import random
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class DecisionType(Enum):
    TRADE = "TRADE"
    NO_TRADE = "NO_TRADE"


@dataclass
class TradingDecision:
    """Structured trading decision from LLM."""
    decision: DecisionType
    actions: list[Dict[str, Any]]
    stop_loss: float
    leverage: float
    rationale: str
    raw_response: str

    @classmethod
    def from_json(cls, data: Dict[str, Any], raw: str = ""):
        """Parse JSON response into TradingDecision."""
        return cls(
            decision=DecisionType(data["decision"]),
            actions=data.get("actions", []),
            stop_loss=data.get("stop_loss", 0.01),
            leverage=data.get("leverage", 1.0),
            rationale=data.get("rationale", "")[:220],  # Enforce 220 char limit
            raw_response=raw
        )


class LLMClient:
    """Base class for LLM trading decision generators."""

    def get_decision(self, prompt: str, market_data: Dict[str, Any]) -> TradingDecision:
        """Generate trading decision given prompt and market data."""
        raise NotImplementedError


class LocalHeuristicLLM(LLMClient):
    """
    Mock LLM for testing that uses simple heuristics.

    Rules:
    - Random walk with 60% NO_TRADE bias
    - When trading: 70% long, 30% short
    - Leverage between 1.0-1.5
    - Stop-loss 1-2%
    """

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def get_decision(self, prompt: str, market_data: Dict[str, Any]) -> TradingDecision:
        """Generate mock decision using heuristics."""

        # 60% NO_TRADE
        if self.rng.random() < 0.6:
            response = {
                "decision": "NO_TRADE",
                "actions": [],
                "rationale": "Market conditions unclear; waiting for better setup."
            }
            return TradingDecision.from_json(response, json.dumps(response))

        # Decide direction
        direction = "long" if self.rng.random() < 0.7 else "short"
        symbol = market_data.get("symbol", "BTC")
        price = market_data.get("price", 50000.0)

        # Random leverage and stop
        leverage = round(self.rng.uniform(1.0, 1.5), 2)
        stop_pct = round(self.rng.uniform(0.01, 0.02), 4)

        response = {
            "decision": "TRADE",
            "actions": [
                {
                    "type": direction,
                    "symbol": symbol,
                    "size": 0.1,  # 10% of equity
                    "entry_price": price
                }
            ],
            "stop_loss": stop_pct,
            "leverage": leverage,
            "rationale": f"Heuristic {direction} signal on {symbol} at {price:.2f}."
        }

        return TradingDecision.from_json(response, json.dumps(response))


class OpenAILLM(LLMClient):
    """OpenAI GPT-4 client for trading decisions."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

    def get_decision(self, prompt: str, market_data: Dict[str, Any]) -> TradingDecision:
        """Query OpenAI API for trading decision."""
        try:
            import openai
            openai.api_key = self.api_key

            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(market_data)}
            ]

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            raw = response.choices[0].message.content
            data = json.loads(raw)
            return TradingDecision.from_json(data, raw)

        except Exception as e:
            # Fail safe to NO_TRADE on error
            fallback = {
                "decision": "NO_TRADE",
                "actions": [],
                "rationale": f"LLM error: {str(e)[:200]}"
            }
            return TradingDecision.from_json(fallback, str(e))


class DeepSeekLLM(LLMClient):
    """DeepSeek API client for trading decisions."""

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment")

    def get_decision(self, prompt: str, market_data: Dict[str, Any]) -> TradingDecision:
        """Query DeepSeek API for trading decision."""
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": json.dumps(market_data)}
                ],
                "temperature": 0.7,
                "response_format": {"type": "json_object"}
            }

            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            raw = response.json()["choices"][0]["message"]["content"]
            data = json.loads(raw)
            return TradingDecision.from_json(data, raw)

        except Exception as e:
            # Fail safe to NO_TRADE on error
            fallback = {
                "decision": "NO_TRADE",
                "actions": [],
                "rationale": f"LLM error: {str(e)[:200]}"
            }
            return TradingDecision.from_json(fallback, str(e))


def get_llm_client(provider: str = "mock", **kwargs) -> LLMClient:
    """
    Factory function to create LLM client.

    Args:
        provider: One of "mock", "openai", "deepseek"
        **kwargs: Provider-specific arguments

    Returns:
        LLMClient instance
    """
    providers = {
        "mock": LocalHeuristicLLM,
        "openai": OpenAILLM,
        "deepseek": DeepSeekLLM
    }

    if provider not in providers:
        raise ValueError(f"Unknown provider: {provider}. Choose from {list(providers.keys())}")

    return providers[provider](**kwargs)
