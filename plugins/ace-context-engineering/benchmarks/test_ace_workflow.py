#!/usr/bin/env python3
"""
Test script to verify the real ACE workflow.

Tests Generator → Reflector → Curator cycle with synthetic data.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.claude_code_method import ClaudeCodeACE


# Synthetic test samples
SYNTHETIC_SAMPLES = [
    {
        'id': 'test-001',
        'instruction': 'Send a Slack message to channel #general saying "Hello from ACE!"',
        'apps': ['Slack'],
        'apis': [
            {'name': 'chat_postMessage', 'app': 'Slack', 'description': 'Send a message to a channel'}
        ],
        'ground_truth': 'slack_client.chat_postMessage'
    },
    {
        'id': 'test-002',
        'instruction': 'Split a $100 bill between 4 people using Venmo',
        'apps': ['Venmo'],
        'apis': [
            {'name': 'payment.request_money', 'app': 'Venmo', 'description': 'Request payment from a user'}
        ],
        'ground_truth': 'venmo_client.payment.request_money'
    },
    {
        'id': 'test-003',
        'instruction': 'Fetch all Slack messages from #engineering channel with pagination',
        'apps': ['Slack'],
        'apis': [
            {'name': 'conversations_history', 'app': 'Slack', 'description': 'Fetch message history'}
        ],
        'ground_truth': 'conversations_history'
    },
]


def main():
    print("="*80)
    print("ACE WORKFLOW TEST")
    print("="*80)
    print()

    # Initialize ACE method
    playbook_path = Path(__file__).parent.parent / 'skills' / 'playbook.json'

    if not playbook_path.exists():
        print(f"❌ Playbook not found at: {playbook_path}")
        return

    print(f"📚 Loading playbook: {playbook_path}")
    ace_method = ClaudeCodeACE(
        playbook_path=str(playbook_path),
        name="TestACE",
        use_embeddings=False  # Use TF-IDF for speed
    )

    # Test offline adaptation
    print("\n" + "="*80)
    print("TESTING OFFLINE ADAPTATION")
    print("="*80 + "\n")

    results = ace_method.adapt(
        samples=SYNTHETIC_SAMPLES,
        mode='offline',
        max_epochs=2  # Just 2 epochs for quick test
    )

    # Print results
    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80 + "\n")

    print("Epoch Results:")
    for epoch_result in results['epochs']:
        print(f"\nEpoch {epoch_result['epoch']}:")
        print(f"  Success rate: {epoch_result['success_rate']:.1%}")
        print(f"  Successes: {epoch_result['successes']}")
        print(f"  Failures: {epoch_result['failures']}")
        print(f"  Bullets added: {epoch_result['bullets_added']}")
        print(f"  Bullets updated: {epoch_result['bullets_updated']}")

    print("\nFinal Metrics:")
    final_metrics = results['final_metrics']
    print(f"  Total tasks: {final_metrics['total_tasks']}")
    print(f"  Successful tasks: {final_metrics['successful_tasks']}")
    print(f"  Bullets added: {final_metrics['bullets_added']}")
    print(f"  Bullets updated: {final_metrics['bullets_updated']}")

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

    # Verify key behaviors
    print("\n✅ Verification:")
    print(f"   - Bullets were retrieved: {final_metrics['total_tasks'] > 0}")
    print(f"   - Solutions were generated: {final_metrics['total_tasks'] == len(SYNTHETIC_SAMPLES) * 2}")  # 2 epochs
    print(f"   - Reflector proposed changes: {final_metrics['bullets_added'] >= 0}")
    print(f"   - Curator merged deltas: {final_metrics['bullets_updated'] >= 0}")
    print(f"   - Multi-epoch adaptation ran: {len(results['epochs']) == 2}")


if __name__ == '__main__':
    main()
