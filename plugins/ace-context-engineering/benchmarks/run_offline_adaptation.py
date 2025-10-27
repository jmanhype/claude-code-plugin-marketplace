#!/usr/bin/env python3
"""
Run offline adaptation on AppWorld training data.

This script demonstrates the full ACE cycle with:
- FAISS-based semantic deduplication
- Three-stage quality-gated curator
- Multi-epoch learning
- Grow-and-refine mechanism
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add benchmarks to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.appworld_loader import AppWorldLoader
from utils.claude_code_method import ClaudeCodeACE
from utils.appworld_executor import create_appworld_executor


def main():
    """Run offline adaptation experiment."""

    print("\n" + "="*80)
    print("ACE Offline Adaptation on AppWorld Training Set")
    print("="*80)
    print("Components:")
    print("  - Generator: BulletRetriever → AppWorldExecutor (Interactive Protocol)")
    print("  - Reflector: Error analysis → Delta proposal")
    print("  - Curator: Three-stage quality gating (FAISS deduplication)")
    print("  - Adaptation: Multi-epoch learning with grow-and-refine")
    print("="*80 + "\n")

    # Configuration
    data_root = Path(__file__).parent / "data"
    playbook_path = Path(__file__).parent.parent / "skills" / "playbook.json"
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)

    # Experiment parameters
    MAX_SAMPLES = int(os.getenv('MAX_SAMPLES', '10'))  # Start small for testing
    MAX_EPOCHS = int(os.getenv('MAX_EPOCHS', '2'))  # 2 epochs to see adaptation
    USE_FAISS = os.getenv('USE_FAISS', 'true').lower() == 'true'

    print(f"⚙️  Configuration:")
    print(f"   Data root: {data_root}")
    print(f"   Playbook: {playbook_path.name}")
    print(f"   Max samples: {MAX_SAMPLES}")
    print(f"   Max epochs: {MAX_EPOCHS}")
    print(f"   FAISS deduplication: {USE_FAISS}")
    print(f"   Results dir: {results_dir}")
    print()

    # Load training data
    print("📥 Loading training data...")
    loader = AppWorldLoader(str(data_root))

    try:
        train_samples = loader.load_split('train', max_samples=MAX_SAMPLES)
    except FileNotFoundError as e:
        print(f"❌ Error loading data: {e}")
        print(f"   Make sure AppWorld data is downloaded to: {data_root}")
        sys.exit(1)

    if not train_samples:
        print("❌ No training samples loaded!")
        sys.exit(1)

    print(f"✓ Loaded {len(train_samples)} training samples\n")

    # Initialize AppWorldExecutor
    print("🔧 Initializing AppWorldExecutor...")

    try:
        executor = create_appworld_executor(
            playbook_path=str(playbook_path),
            request_dir="/tmp/appworld_requests",
            max_turns=3,
            timeout_per_turn=300,
            use_ace_generator=True,  # CRITICAL: This closes the learning loop!
            use_faiss=USE_FAISS
        )
        print("✓ Created AppWorldExecutor with ACECodeGenerator (LEARNING LOOP CLOSED!)")
    except Exception as e:
        print(f"❌ Error creating executor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Initialize ACE method
    print("🔧 Initializing ACE method...")

    try:
        ace = ClaudeCodeACE(
            playbook_path=str(playbook_path),
            name="ACE_AppWorld_OfflineAdaptation",
            executor=executor,
            use_faiss=USE_FAISS
        )
    except Exception as e:
        print(f"❌ Error initializing ACE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print(f"✓ Initialized ACE")
    print(f"   Starting playbook bullets: {len(ace.playbook.get('bullets', []))}")
    print(f"   Curator using: {'FAISS' if ace.curator.using_faiss else 'TF-IDF fallback'}")
    print()

    # Create experiment metadata
    experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    metadata = {
        'experiment_id': experiment_id,
        'timestamp': datetime.now().isoformat(),
        'config': {
            'max_samples': MAX_SAMPLES,
            'max_epochs': MAX_EPOCHS,
            'use_faiss': USE_FAISS,
            'playbook_path': str(playbook_path),
            'data_root': str(data_root)
        },
        'train_samples': len(train_samples),
        'initial_bullets': len(ace.playbook.get('bullets', []))
    }

    # Save initial playbook
    initial_playbook_path = results_dir / f"playbook_initial_{experiment_id}.json"
    with open(initial_playbook_path, 'w') as f:
        json.dump(ace.playbook, f, indent=2)
    print(f"💾 Saved initial playbook: {initial_playbook_path.name}\n")

    # Run offline adaptation
    print("🚀 Starting offline adaptation...\n")

    try:
        results = ace.adapt(
            samples=train_samples,
            mode='offline',
            max_epochs=MAX_EPOCHS
        )
    except Exception as e:
        print(f"\n❌ Error during adaptation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Save final playbook
    final_playbook_path = results_dir / f"playbook_final_{experiment_id}.json"
    with open(final_playbook_path, 'w') as f:
        json.dump(ace.playbook, f, indent=2)
    print(f"\n💾 Saved final playbook: {final_playbook_path.name}")

    # Save epoch snapshots
    print(f"\n💾 Epoch snapshots saved:")
    for snapshot in ace.epoch_snapshots:
        print(f"   - Epoch {snapshot['epoch']}: {snapshot['num_bullets']} bullets")

    # Compile final results
    final_metrics = ace.get_metrics()

    metadata['results'] = {
        'final_metrics': final_metrics,
        'epochs': results.get('epochs', []),
        'final_bullets': len(ace.playbook.get('bullets', [])),
        'epoch_snapshots': ace.epoch_snapshots
    }

    # Save results
    results_path = results_dir / f"offline_adaptation_{experiment_id}.json"
    with open(results_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n💾 Saved results: {results_path.name}")

    # Print summary
    print("\n" + "="*80)
    print("OFFLINE ADAPTATION SUMMARY")
    print("="*80)

    print(f"\n📊 Overall Metrics:")
    print(f"   Total tasks: {final_metrics['total_tasks']}")
    print(f"   Successful: {final_metrics['successful_tasks']}")
    print(f"   Success rate: {final_metrics['success_rate']:.1%}")
    print(f"   Bullets added: {final_metrics['bullets_added']}")
    print(f"   Bullets updated: {final_metrics['bullets_updated']}")

    print(f"\n📈 Epoch Progression:")
    for i, epoch_data in enumerate(results.get('epochs', [])):
        print(f"   Epoch {i+1}:")
        print(f"      Success rate: {epoch_data['success_rate']:.1%}")
        print(f"      Bullets added: {epoch_data['bullets_added']}")
        print(f"      Bullets updated: {epoch_data['bullets_updated']}")

    print(f"\n📚 Playbook Evolution:")
    print(f"   Initial bullets: {metadata['initial_bullets']}")
    print(f"   Final bullets: {metadata['results']['final_bullets']}")
    print(f"   Change: +{metadata['results']['final_bullets'] - metadata['initial_bullets']}")

    print(f"\n💾 Output Files:")
    print(f"   Initial playbook: {initial_playbook_path}")
    print(f"   Final playbook: {final_playbook_path}")
    print(f"   Results JSON: {results_path}")

    print("\n" + "="*80)
    print("✅ OFFLINE ADAPTATION COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
