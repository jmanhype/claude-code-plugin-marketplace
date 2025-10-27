"""
AppWorld Evaluation Harness for ACE

Evaluates ACE framework on AppWorld benchmark following the paper's methodology:
1. Baseline: ReAct without ACE
2. Offline Adaptation: Train on train split, evaluate on test splits
3. Metrics: TGC (Task Goal Completion) and SGC (Scenario Goal Completion)

Based on ACE paper (arXiv:2510.04618v1, Section 4.3)
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add benchmarks to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.appworld_executor import AppWorldExecutor, APPWORLD_AVAILABLE
from utils.appworld_loader import AppWorldLoader
from utils.claude_code_method import ClaudeCodeACE


def run_baseline_evaluation(
    test_samples: List[Dict],
    executor: AppWorldExecutor,
    max_samples: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run baseline evaluation (ReAct without ACE).

    Args:
        test_samples: List of test samples
        executor: AppWorld executor
        max_samples: Maximum number of samples to evaluate (for testing)

    Returns:
        {
            'tgc': average TGC,
            'sgc': average SGC,
            'results': list of per-sample results
        }
    """
    print("\n" + "="*70)
    print("BASELINE EVALUATION (ReAct without ACE)")
    print("="*70)

    if max_samples:
        test_samples = test_samples[:max_samples]

    results = []
    total_tgc = 0.0
    total_sgc = 0.0

    for idx, sample in enumerate(test_samples, 1):
        task_id = sample['task_id']
        instruction = sample['instruction']

        print(f"\n[{idx}/{len(test_samples)}] Task: {task_id}")
        print(f"Instruction: {instruction[:100]}...")

        try:
            # Execute without playbook bullets (baseline)
            result = executor.solve_task(
                instruction=instruction,
                apps=sample.get('apps', []),
                apis=sample.get('apis', []),
                playbook_bullets=[],  # No ACE guidance
                ground_truth=sample.get('ground_truth'),
                task_id=task_id
            )

            tgc = result.get('tgc', 0.0)
            sgc = result.get('sgc', 0.0)
            success = result.get('success', False)

            total_tgc += tgc
            total_sgc += sgc

            results.append({
                'task_id': task_id,
                'tgc': tgc,
                'sgc': sgc,
                'success': success
            })

            print(f"  TGC: {tgc:.2f}, SGC: {sgc:.2f}, Success: {success}")

        except Exception as e:
            print(f"  ERROR: {str(e)}")
            results.append({
                'task_id': task_id,
                'tgc': 0.0,
                'sgc': 0.0,
                'success': False,
                'error': str(e)
            })

    avg_tgc = (total_tgc / len(results)) * 100 if results else 0.0
    avg_sgc = (total_sgc / len(results)) * 100 if results else 0.0

    print(f"\n{'='*70}")
    print(f"BASELINE RESULTS:")
    print(f"  Average TGC: {avg_tgc:.1f}%")
    print(f"  Average SGC: {avg_sgc:.1f}%")
    print(f"  Total samples: {len(results)}")
    print(f"{'='*70}")

    return {
        'tgc': avg_tgc,
        'sgc': avg_sgc,
        'results': results
    }


def run_ace_offline_evaluation(
    train_samples: List[Dict],
    test_samples: List[Dict],
    playbook_path: str,
    max_train_samples: Optional[int] = None,
    max_test_samples: Optional[int] = None,
    max_epochs: int = 5
) -> Dict[str, Any]:
    """
    Run ACE offline adaptation evaluation.

    Paper methodology (Section 4.1):
    1. Train on train split (offline adaptation)
    2. Evaluate on test split with learned playbook

    Args:
        train_samples: Training samples for offline adaptation
        test_samples: Test samples for evaluation
        playbook_path: Path to playbook file
        max_train_samples: Max training samples (for testing)
        max_test_samples: Max test samples (for testing)
        max_epochs: Maximum epochs for offline adaptation

    Returns:
        {
            'tgc': average TGC,
            'sgc': average SGC,
            'training_stats': adaptation statistics,
            'results': list of per-sample results
        }
    """
    print("\n" + "="*70)
    print("ACE OFFLINE ADAPTATION")
    print("="*70)

    if max_train_samples:
        train_samples = train_samples[:max_train_samples]
    if max_test_samples:
        test_samples = test_samples[:max_test_samples]

    # Initialize ACE with AppWorld executor
    executor = AppWorldExecutor(experiment_name="ace_offline_eval")
    ace = ClaudeCodeACE(
        playbook_path=playbook_path,
        executor=executor,
        use_faiss=True
    )

    # Phase 1: Offline adaptation on training data
    print(f"\n📚 Training on {len(train_samples)} samples (max {max_epochs} epochs)...")
    training_results = ace.adapt(
        train_samples,
        mode='offline',
        max_epochs=max_epochs
    )

    print(f"\n✅ Training complete!")
    print(f"  Final playbook bullets: {training_results.get('final_bullet_count', 0)}")
    print(f"  Epochs completed: {training_results.get('epochs_completed', 0)}")

    # Phase 2: Evaluate on test data with learned playbook
    print(f"\n🧪 Evaluating on {len(test_samples)} test samples...")

    results = []
    total_tgc = 0.0
    total_sgc = 0.0

    for idx, sample in enumerate(test_samples, 1):
        task_id = sample['task_id']
        instruction = sample['instruction']

        print(f"\n[{idx}/{len(test_samples)}] Task: {task_id}")
        print(f"Instruction: {instruction[:100]}...")

        try:
            # Generate with learned playbook
            generation_result = ace.generate(sample)

            tgc = generation_result['execution_result'].get('tgc', 0.0)
            sgc = generation_result['execution_result'].get('sgc', 0.0)
            success = generation_result['execution_result'].get('success', False)

            total_tgc += tgc
            total_sgc += sgc

            results.append({
                'task_id': task_id,
                'tgc': tgc,
                'sgc': sgc,
                'success': success,
                'bullets_used': len(generation_result.get('retrieved_bullets', []))
            })

            print(f"  TGC: {tgc:.2f}, SGC: {sgc:.2f}, Success: {success}")
            print(f"  Bullets used: {len(generation_result.get('retrieved_bullets', []))}")

        except Exception as e:
            print(f"  ERROR: {str(e)}")
            results.append({
                'task_id': task_id,
                'tgc': 0.0,
                'sgc': 0.0,
                'success': False,
                'error': str(e)
            })

    avg_tgc = (total_tgc / len(results)) * 100 if results else 0.0
    avg_sgc = (total_sgc / len(results)) * 100 if results else 0.0

    print(f"\n{'='*70}")
    print(f"ACE OFFLINE RESULTS:")
    print(f"  Average TGC: {avg_tgc:.1f}%")
    print(f"  Average SGC: {avg_sgc:.1f}%")
    print(f"  Total samples: {len(results)}")
    print(f"{'='*70}")

    return {
        'tgc': avg_tgc,
        'sgc': avg_sgc,
        'training_stats': training_results,
        'results': results
    }


def main():
    """Run full evaluation pipeline."""

    # Check AppWorld availability
    if not APPWORLD_AVAILABLE:
        print("❌ AppWorld is not available. Please install AppWorld first.")
        print("   See: https://github.com/stonybrooknlp/appworld")
        return

    # Configuration
    MAX_TRAIN_SAMPLES = int(os.environ.get('MAX_TRAIN_SAMPLES', '90'))  # Paper uses 90
    MAX_TEST_SAMPLES = int(os.environ.get('MAX_TEST_SAMPLES', '168'))  # Full test-normal
    MAX_EPOCHS = int(os.environ.get('MAX_EPOCHS', '5'))
    RUN_BASELINE = os.environ.get('RUN_BASELINE', 'true').lower() == 'true'
    RUN_ACE = os.environ.get('RUN_ACE', 'true').lower() == 'true'

    # Setup paths
    benchmarks_dir = Path(__file__).parent
    playbook_path = benchmarks_dir / "data" / "playbooks" / "appworld_playbook.json"
    results_dir = benchmarks_dir / "results"
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"appworld_eval_{timestamp}.json"

    print("="*70)
    print("ACE APPWORLD EVALUATION HARNESS")
    print("="*70)
    print(f"Configuration:")
    print(f"  Max train samples: {MAX_TRAIN_SAMPLES}")
    print(f"  Max test samples: {MAX_TEST_SAMPLES}")
    print(f"  Max epochs: {MAX_EPOCHS}")
    print(f"  Run baseline: {RUN_BASELINE}")
    print(f"  Run ACE: {RUN_ACE}")
    print(f"  Playbook: {playbook_path}")
    print(f"  Results will be saved to: {results_file}")

    # Load data
    print(f"\n📂 Loading AppWorld data...")

    # Get AppWorld data root from environment
    appworld_root = os.environ.get('APPWORLD_ROOT', '/tmp/appworld')
    appworld_data = os.path.join(appworld_root, 'data')

    if not os.path.exists(appworld_data):
        print(f"❌ AppWorld data directory not found: {appworld_data}")
        print(f"   Please ensure APPWORLD_ROOT is set correctly.")
        return

    loader = AppWorldLoader(appworld_data)

    train_samples = loader.load_split('train', max_samples=MAX_TRAIN_SAMPLES)
    test_normal_samples = loader.load_split('test_normal', max_samples=MAX_TEST_SAMPLES)

    print(f"  Loaded {len(train_samples)} training samples")
    print(f"  Loaded {len(test_normal_samples)} test-normal samples")

    evaluation_results = {
        'timestamp': timestamp,
        'config': {
            'max_train_samples': MAX_TRAIN_SAMPLES,
            'max_test_samples': MAX_TEST_SAMPLES,
            'max_epochs': MAX_EPOCHS
        },
        'splits': {
            'train_count': len(train_samples),
            'test_normal_count': len(test_normal_samples)
        }
    }

    # Run baseline evaluation
    if RUN_BASELINE:
        executor = AppWorldExecutor(experiment_name="baseline_eval")
        baseline_results = run_baseline_evaluation(
            test_normal_samples,
            executor,
            max_samples=MAX_TEST_SAMPLES
        )
        evaluation_results['baseline'] = baseline_results

    # Run ACE offline evaluation
    if RUN_ACE:
        ace_results = run_ace_offline_evaluation(
            train_samples,
            test_normal_samples,
            str(playbook_path),
            max_train_samples=MAX_TRAIN_SAMPLES,
            max_test_samples=MAX_TEST_SAMPLES,
            max_epochs=MAX_EPOCHS
        )
        evaluation_results['ace_offline'] = ace_results

    # Compute improvements
    if RUN_BASELINE and RUN_ACE:
        baseline_tgc = evaluation_results['baseline']['tgc']
        baseline_sgc = evaluation_results['baseline']['sgc']
        ace_tgc = evaluation_results['ace_offline']['tgc']
        ace_sgc = evaluation_results['ace_offline']['sgc']

        tgc_improvement = ace_tgc - baseline_tgc
        sgc_improvement = ace_sgc - baseline_sgc

        evaluation_results['improvements'] = {
            'tgc': tgc_improvement,
            'sgc': sgc_improvement
        }

        print("\n" + "="*70)
        print("FINAL COMPARISON")
        print("="*70)
        print(f"Baseline TGC: {baseline_tgc:.1f}%")
        print(f"ACE TGC:      {ace_tgc:.1f}% ({tgc_improvement:+.1f}%)")
        print(f"")
        print(f"Baseline SGC: {baseline_sgc:.1f}%")
        print(f"ACE SGC:      {ace_sgc:.1f}% ({sgc_improvement:+.1f}%)")
        print("="*70)

        # Compare with paper results (Table 1)
        paper_baseline_avg = 42.4  # ReAct baseline average
        paper_ace_avg = 59.4  # ReAct + ACE average
        paper_improvement = paper_ace_avg - paper_baseline_avg

        our_baseline_avg = (baseline_tgc + baseline_sgc) / 2
        our_ace_avg = (ace_tgc + ace_sgc) / 2
        our_improvement = our_ace_avg - our_baseline_avg

        print(f"\nComparison with paper (Table 1):")
        print(f"  Paper improvement: +{paper_improvement:.1f}%")
        print(f"  Our improvement:   +{our_improvement:.1f}%")

    # Save results
    with open(results_file, 'w') as f:
        json.dump(evaluation_results, f, indent=2)

    print(f"\n✅ Results saved to: {results_file}")


if __name__ == "__main__":
    main()
