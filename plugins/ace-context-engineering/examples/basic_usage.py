#!/usr/bin/env python3
"""Basic usage example for ACE package."""

import json
import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ace.clients import DummyLLMClient, LLMResponse
from ace.delta import DeltaOperation, DeltaBatch
from ace.retrieval import retrieve_bullets


def example_dummy_client():
    """Example: Using DummyLLMClient for testing."""
    print("=== Example 1: DummyLLMClient ===")

    client = DummyLLMClient()
    client.queue('{"new_bullets": [], "reasoning": "No updates needed"}')
    client.queue('{"status": "success", "message": "Task completed"}')

    response1 = client.complete("Generate delta")
    print(f"Response 1: {response1.text}")

    response2 = client.complete("Check status")
    print(f"Response 2: {response2.text}")
    print()


def example_delta_operations():
    """Example: Creating and serializing delta operations."""
    print("=== Example 2: Delta Operations ===")

    op1 = DeltaOperation(
        type="ADD",
        section="bullets",
        content="Always validate input data before processing",
        bullet_id="bullet-2025-10-26-002",
        metadata={"priority": 1}
    )

    op2 = DeltaOperation(
        type="UPDATE",
        section="bullets",
        bullet_id="bullet-2025-10-25-001",
        metadata={"helpful_delta": 1}
    )

    batch = DeltaBatch(
        reasoning="Adding validation guidance based on recent errors",
        operations=[op1, op2]
    )

    print("Delta Batch JSON:")
    print(json.dumps(batch.to_json(), indent=2))
    print()


def example_retrieval():
    """Example: Retrieving bullets with TF-IDF + tags."""
    print("=== Example 3: Bullet Retrieval ===")

    # Load playbook
    playbook_path = Path(__file__).parent.parent / "skills" / "playbook.json"
    if not playbook_path.exists():
        print(f"Playbook not found at {playbook_path}")
        return

    with open(playbook_path) as f:
        data = json.load(f)
        bullets = data.get("bullets", data)

    # Retrieve bullets for a query
    query = "editing files with proper validation"
    tags = ["tool.edit", "validation"]

    results = retrieve_bullets(bullets, query, tags=tags, top_k=3)

    print(f"Query: {query}")
    print(f"Tags: {tags}")
    print(f"\\nTop {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\\n{i}. {result.title}")
        print(f"   ID: {result.bullet_id}")
        print(f"   Score: {result.score:.4f}")
        print(f"   Tags: {', '.join(result.tags[:3])}...")
    print()


if __name__ == "__main__":
    example_dummy_client()
    example_delta_operations()
    example_retrieval()
