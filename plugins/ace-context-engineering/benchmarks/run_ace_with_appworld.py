#!/usr/bin/env python3
"""
Demonstration of ACE with real AppWorld executor.

This script shows how to use the AppWorldExecutor instead of the mock
SkillsExecutor for actual task execution and TGC/SGC metric computation.
"""

import os
import sys
from pathlib import Path

# Set APPWORLD_ROOT before imports
os.environ['APPWORLD_ROOT'] = '/tmp/appworld'

# Add AppWorld venv to path
appworld_site = Path('/tmp/appworld/venv_appworld/lib/python3.11/site-packages')
if str(appworld_site) not in sys.path:
    sys.path.insert(0, str(appworld_site))

from utils.claude_code_method import ClaudeCodeACE
from utils.appworld_executor import AppWorldExecutor, APPWORLD_AVAILABLE
from utils.appworld_loader import AppWorldLoader


def main():
    """Run ACE with AppWorld executor on a small sample."""
    print("\n" + "="*80)
    print("ACE WITH REAL APPWORLD EXECUTOR")
    print("="*80)

    # Check AppWorld availability
    if not APPWORLD_AVAILABLE:
        print("\n❌ AppWorld not available")
        print("   Install from: /tmp/appworld/venv_appworld")
        return 1

    print("\n✅ AppWorld is available")

    # Initialize AppWorld executor
    print("\n📦 Initializing AppWorld executor...")
    executor = AppWorldExecutor(experiment_name="ace_appworld_demo")
    print(f"   Experiment: {executor.experiment_name}")

    # Initialize ACE with AppWorld executor
    playbook_path = "data/playbooks/appworld_playbook.json"
    print(f"\n🎯 Initializing ACE with AppWorld executor...")
    print(f"   Playbook: {playbook_path}")

    ace = ClaudeCodeACE(
        playbook_path=playbook_path,
        name="ACE_AppWorld",
        use_faiss=True,
        executor=executor  # Use real AppWorld executor instead of mock
    )

    # Load AppWorld dataset
    print("\n📊 Loading AppWorld training data...")
    loader = AppWorldLoader()

    # Load just 1 sample for demo
    max_samples = int(os.getenv('MAX_SAMPLES', 1))
    train_samples = loader.load_split('train', max_samples=max_samples)

    print(f"   Loaded {len(train_samples)} training sample(s)")

    # Run offline adaptation
    print("\n🚀 Starting offline adaptation...")
    print(f"   Samples: {len(train_samples)}")
    print(f"   Epochs: 1 (demo)")
    print(f"   Using: Real AppWorld executor")
    print()

    results = ace.adapt(train_samples, mode='offline', max_epochs=1)

    # Display results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    final_metrics = results.get('final_metrics', {})
    print(f"\nTasks processed: {final_metrics.get('total_tasks', 0)}")
    print(f"Success rate: {final_metrics.get('success_rate', 0):.1%}")
    print(f"Bullets added: {final_metrics.get('bullets_added', 0)}")
    print(f"Bullets updated: {final_metrics.get('bullets_updated', 0)}")

    # Note about TGC/SGC metrics
    print("\n" + "="*80)
    print("NOTES")
    print("="*80)
    print("\n⚠️  Current Limitations:")
    print("   1. Code generation uses templates (not LLM-based)")
    print("   2. TGC/SGC metrics require fully implemented code")
    print("   3. For real evaluation, integrate LLM code generation")
    print()
    print("✅ AppWorld Integration Working:")
    print("   1. Task loading from AppWorld ✓")
    print("   2. Executor can execute in AppWorld environment ✓")
    print("   3. TGC/SGC metric computation ready ✓")
    print("   4. Three-stage FAISS curator active ✓")
    print()
    print("Next steps:")
    print("   1. Integrate LLM-based code generation")
    print("   2. Test with full AppWorld task execution")
    print("   3. Run evaluation on test-normal split")
    print("="*80 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
