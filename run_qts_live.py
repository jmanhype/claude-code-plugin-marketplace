#!/usr/bin/env python3
"""
Run QTS with real LLM using .env API keys
"""
import os
import sys
from pathlib import Path

# Load .env file
from dotenv import load_dotenv
load_dotenv()

# Verify API key is loaded
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("ERROR: GEMINI_API_KEY not found in .env file")
    sys.exit(1)

print("✅ GEMINI_API_KEY loaded from .env")
print(f"   Key prefix: {api_key[:20]}...")

# Run the orchestrator
print("\n🚀 Starting QTS with Gemini (Google)...")
print("   Mode: Execute only (single tick)")
print("   Symbols: BTC")
print("   Execution: Paper trading")
print("   Market data: Mock (safe testing)")
print()

os.system("python -m qts.main --symbols BTC --llm-provider gemini --execution-mode paper")
