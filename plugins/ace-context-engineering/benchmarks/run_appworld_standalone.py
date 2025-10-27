#!/usr/bin/env python3
"""
Standalone ACE AppWorld benchmark runner for CI/CD.

This script runs ACE benchmarks without requiring interactive Claude Code.
It uses the ACECodeGenerator directly with the Anthropic API.

Usage:
    python -m benchmarks.run_appworld_standalone \
        --split dev \
        --max-samples 5 \
        --playbook skills/playbook.json \
        --output results/run.json
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import ACE components
try:
    from benchmarks.utils.ace_code_generator import ACECodeGenerator
    from benchmarks.utils.appworld_loader import AppWorldLoader
    from benchmarks.utils.claude_code_react_agent import ClaudeCodeReActAgent
except ImportError as e:
    print(f"❌ Failed to import ACE components: {e}")
    print(f"   Make sure you're running from the ACE plugin directory")
    sys.exit(1)


def setup_appworld_environment():
    """Setup AppWorld environment and check availability."""
    try:
        # Try to import AppWorld
        sys.path.insert(0, "/tmp/appworld/venv_appworld/lib/python3.11/site-packages")
        from appworld import AppWorld
        print(f"✅ AppWorld available")
        return True
    except ImportError:
        print(f"⚠️  AppWorld not available - will only test code generation")
        return False


def run_benchmark(
    split: str,
    max_samples: int,
    playbook_path: Path,
    data_root: Path,
    output_path: Path,
    execute_in_appworld: bool = True
) -> Dict[str, Any]:
    """
    Run ACE benchmark on AppWorld tasks.

    Args:
        split: Dataset split (dev/train/test_normal/test_challenge)
        max_samples: Maximum number of tasks to run
        playbook_path: Path to playbook.json
        data_root: Path to AppWorld data root
        output_path: Where to save results
        execute_in_appworld: Whether to actually execute (requires AppWorld)

    Returns:
        Results dictionary
    """
    print(f"\n{'='*70}")
    print(f"ACE APPWORLD BENCHMARK")
    print(f"{'='*70}")
    print(f"Split: {split}")
    print(f"Max samples: {max_samples}")
    print(f"Playbook: {playbook_path}")
    print(f"Data root: {data_root}")
    print(f"Execute: {execute_in_appworld}")
    print(f"{'='*70}\n")

    # Load dataset
    try:
        loader = AppWorldLoader(str(data_root))
        samples = loader.load_split(split, max_samples=max_samples)
        print(f"✅ Loaded {len(samples)} samples from {split} split\n")
    except Exception as e:
        print(f"❌ Failed to load dataset: {e}")
        return {
            "error": str(e),
            "split": split,
            "max_samples": max_samples,
            "samples_loaded": 0
        }

    # Initialize agent
    try:
        agent = ClaudeCodeReActAgent(
            playbook_path=str(playbook_path),
            use_ace_generator=True,
            use_faiss=False  # Use TF-IDF for CI/CD simplicity
        )
        print(f"✅ Agent initialized\n")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return {
            "error": str(e),
            "split": split,
            "samples_loaded": len(samples)
        }

    # Run benchmarks
    results = {
        "metadata": {
            "split": split,
            "max_samples": max_samples,
            "samples_loaded": len(samples),
            "playbook": str(playbook_path),
            "executed_in_appworld": execute_in_appworld,
            "timestamp": time.time()
        },
        "tasks": []
    }

    for i, sample in enumerate(samples, 1):
        task_id = sample['task_id']
        instruction = sample['instruction']
        apps = sample.get('apps', ['general'])

        print(f"\n{'#'*70}")
        print(f"TASK {i}/{len(samples)}: {task_id}")
        print(f"{'#'*70}")
        print(f"Instruction: {instruction[:100]}...")
        print(f"Apps: {', '.join(apps)}")
        print(f"{'#'*70}\n")

        try:
            # Run task
            result = agent.solve_task(
                instruction=instruction,
                apps=apps,
                app_descriptions={},  # Not needed for ACE generator
                task_id=task_id,
                ground_truth=sample.get('ground_truth', ''),
                apis=sample.get('apis', []),
                playbook_bullets=None  # Let agent retrieve from playbook
            )

            # Add to results
            task_result = {
                "task_id": task_id,
                "instruction": instruction,
                "apps": apps,
                "success": result.get('success', False),
                "tgc": result.get('tgc', 0.0),
                "sgc": result.get('sgc', 0.0),
                "turns": result.get('turns', 0),
                "used_bullet_ids": result.get('used_bullet_ids', []),
                "bullet_feedback": result.get('bullet_feedback', {}),
                "code_length": len(result.get('code', '')),
                "final_answer": result.get('final_answer', '')
            }

            results["tasks"].append(task_result)

            print(f"\n📊 TASK RESULT:")
            print(f"  Success: {'✅' if task_result['success'] else '❌'}")
            print(f"  TGC: {task_result['tgc']:.2f}")
            print(f"  SGC: {task_result['sgc']:.2f}")
            print(f"  Turns: {task_result['turns']}")
            print(f"  Bullets: {len(task_result['used_bullet_ids'])}\n")

        except Exception as e:
            print(f"❌ Task failed: {e}")
            import traceback
            traceback.print_exc()

            task_result = {
                "task_id": task_id,
                "instruction": instruction,
                "apps": apps,
                "error": str(e),
                "success": False,
                "tgc": 0.0,
                "sgc": 0.0
            }
            results["tasks"].append(task_result)

    # Calculate aggregate statistics
    successful_tasks = sum(1 for t in results["tasks"] if t.get("success", False))
    avg_tgc = sum(t.get("tgc", 0) for t in results["tasks"]) / len(results["tasks"]) if results["tasks"] else 0
    avg_sgc = sum(t.get("tgc", 0) for t in results["tasks"]) / len(results["tasks"]) if results["tasks"] else 0

    results["metadata"]["summary"] = {
        "total_tasks": len(results["tasks"]),
        "successful_tasks": successful_tasks,
        "success_rate": successful_tasks / len(results["tasks"]) if results["tasks"] else 0,
        "avg_tgc": avg_tgc,
        "avg_sgc": avg_sgc
    }

    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*70}")
    print(f"BENCHMARK COMPLETE")
    print(f"{'='*70}")
    print(f"Total tasks: {len(results['tasks'])}")
    print(f"Successful: {successful_tasks}")
    print(f"Success rate: {successful_tasks / len(results['tasks']) * 100:.1f}%")
    print(f"Avg TGC: {avg_tgc:.2f}")
    print(f"Avg SGC: {avg_sgc:.2f}")
    print(f"\n📁 Results saved to: {output_path}")
    print(f"{'='*70}\n")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Run ACE benchmarks on AppWorld tasks"
    )
    parser.add_argument(
        "--split",
        type=str,
        default="dev",
        choices=["dev", "train", "test_normal", "test_challenge"],
        help="Dataset split to use"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=5,
        help="Maximum number of samples to run"
    )
    parser.add_argument(
        "--playbook",
        type=Path,
        default=Path("skills/playbook.json"),
        help="Path to playbook.json"
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("/tmp/appworld/data"),
        help="Path to AppWorld data root"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/benchmark.json"),
        help="Output path for results"
    )
    parser.add_argument(
        "--no-execute",
        action="store_true",
        help="Only generate code, don't execute in AppWorld"
    )

    args = parser.parse_args()

    # Check AppWorld availability
    appworld_available = setup_appworld_environment()
    execute = appworld_available and not args.no_execute

    if not execute:
        print(f"⚠️  Running in code-generation-only mode")
        print(f"   (AppWorld execution disabled)")

    # Run benchmark
    results = run_benchmark(
        split=args.split,
        max_samples=args.max_samples,
        playbook_path=args.playbook,
        data_root=args.data_root,
        output_path=args.output,
        execute_in_appworld=execute
    )

    # Exit with appropriate code
    if "error" in results:
        sys.exit(1)

    if results.get("metadata", {}).get("summary", {}).get("successful_tasks", 0) == 0:
        print(f"⚠️  No successful tasks")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
