"""
AppWorld Interactive Evaluation Harness for ACE

Uses Claude Code interactive protocol where:
1. AppWorld ReAct agent writes code generation request
2. Claude Code reads request and generates code using Skill
3. Claude Code writes response with generated code
4. AppWorld ReAct agent executes code and provides feedback

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

# Check AppWorld availability
APPWORLD_AVAILABLE = Path("/tmp/appworld").exists()

# Direct imports to avoid utils/__init__.py (which imports FAISS)
import importlib.util

# Load claude_code_react_agent directly
agent_spec = importlib.util.spec_from_file_location(
    "claude_code_react_agent",
    Path(__file__).parent / "utils" / "claude_code_react_agent.py"
)
agent_module = importlib.util.module_from_spec(agent_spec)
agent_spec.loader.exec_module(agent_module)
ClaudeCodeReActAgent = agent_module.ClaudeCodeReActAgent
create_response_file = agent_module.create_response_file

# Load appworld_loader directly
loader_spec = importlib.util.spec_from_file_location(
    "appworld_loader",
    Path(__file__).parent / "utils" / "appworld_loader.py"
)
loader_module = importlib.util.module_from_spec(loader_spec)
loader_spec.loader.exec_module(loader_module)
AppWorldLoader = loader_module.AppWorldLoader


def run_interactive_test(
    test_samples: List[Dict],
    agent: ClaudeCodeReActAgent,
    max_samples: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run test with interactive code generation and execution.

    Args:
        test_samples: List of test samples
        agent: Interactive ReAct agent (with execution capability)
        max_samples: Maximum number of samples to evaluate

    Returns:
        {
            'results': list of per-sample results,
            'total_samples': number of samples processed,
            'avg_tgc': average TGC,
            'avg_sgc': average SGC,
            'success_rate': % of tasks with TGC=1.0
        }
    """
    print("\n" + "="*70)
    print("INTERACTIVE CODE GENERATION + EXECUTION TEST")
    print("="*70)
    print("\nThis test uses the interactive protocol with AppWorld execution:")
    print("1. Agent writes request to /tmp/appworld_requests/request_turn_N.json")
    print("2. Claude Code reads request and generates code using Skill")
    print("3. Claude Code writes response to response_turn_N.json")
    print("4. Agent reads response and executes code in AppWorld")
    print("5. Agent evaluates TGC/SGC metrics")
    print("="*70)

    if max_samples:
        test_samples = test_samples[:max_samples]

    results = []
    total_tgc = 0.0
    total_sgc = 0.0
    successes = 0

    for idx, sample in enumerate(test_samples, 1):
        task_id = sample['task_id']
        instruction = sample['instruction']
        apps = sample.get('apps', [])

        print(f"\n[{idx}/{len(test_samples)}] Task: {task_id}")
        print(f"Instruction: {instruction}")
        print(f"Apps: {', '.join(apps)}")

        try:
            # Get app descriptions (simplified - would come from AppWorld)
            app_descriptions = {
                app: f"{app.capitalize()} API" for app in apps
            }

            # Solve task using interactive protocol + execution
            result = agent.solve_task(
                instruction=instruction,
                apps=apps,
                app_descriptions=app_descriptions,
                task_id=task_id
            )

            tgc = result['tgc']
            sgc = result['sgc']
            success = result['success']

            total_tgc += tgc
            total_sgc += sgc
            if success:
                successes += 1

            print(f"\n✅ Task execution complete!")
            print(f"  TGC: {tgc:.2f}")
            print(f"  SGC: {sgc:.2f}")
            print(f"  Success: {'✅' if success else '❌'}")
            print(f"  Turns: {result['turns']}")
            print(f"  Bullets used: {len(result['bullets_used'])}")

            results.append({
                'task_id': task_id,
                'instruction': instruction,
                'tgc': tgc,
                'sgc': sgc,
                'success': success,
                'turns': result['turns'],
                'code_generated': len(result['code_history']) > 0,
                'bullets_used': len(result['bullets_used'])
            })

        except Exception as e:
            print(f"  ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append({
                'task_id': task_id,
                'error': str(e),
                'tgc': 0.0,
                'sgc': 0.0,
                'success': False
            })

    # Calculate averages
    n = len(results)
    avg_tgc = total_tgc / n if n > 0 else 0.0
    avg_sgc = total_sgc / n if n > 0 else 0.0
    success_rate = (successes / n * 100) if n > 0 else 0.0

    return {
        'results': results,
        'total_samples': len(results),
        'avg_tgc': avg_tgc,
        'avg_sgc': avg_sgc,
        'success_rate': success_rate
    }


def main():
    """Run interactive evaluation test."""

    # Check AppWorld availability (check if data exists, not Python package)
    appworld_root = os.environ.get('APPWORLD_ROOT', '/tmp/appworld')
    appworld_data = os.path.join(appworld_root, 'data')

    if not os.path.exists(appworld_data):
        print(f"❌ AppWorld data directory not found: {appworld_data}")
        print(f"   Please ensure APPWORLD_ROOT is set correctly.")
        return

    # Configuration
    MAX_TEST_SAMPLES = int(os.environ.get('MAX_TEST_SAMPLES', '1'))  # Start with 1 for testing

    # Setup paths
    benchmarks_dir = Path(__file__).parent
    playbook_path = benchmarks_dir / "data" / "playbooks" / "appworld_playbook.json"
    request_dir = "/tmp/appworld_requests"
    results_dir = benchmarks_dir / "results"
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"appworld_interactive_{timestamp}.json"

    print("="*70)
    print("ACE APPWORLD INTERACTIVE EVALUATION")
    print("="*70)
    print(f"Configuration:")
    print(f"  Max test samples: {MAX_TEST_SAMPLES}")
    print(f"  Playbook: {playbook_path}")
    print(f"  Request directory: {request_dir}")
    print(f"  Results will be saved to: {results_file}")

    # Initialize interactive agent
    print(f"\n🤖 Initializing ClaudeCodeReActAgent...")
    agent = ClaudeCodeReActAgent(
        playbook_path=str(playbook_path),
        request_dir=request_dir,
        max_turns=3,  # Allow up to 3 turns per task
        timeout_per_turn=300  # 5 minutes timeout
    )

    # Load data
    print(f"\n📂 Loading AppWorld data...")
    loader = AppWorldLoader(appworld_data)

    test_normal_samples = loader.load_split('test_normal', max_samples=MAX_TEST_SAMPLES)

    print(f"  Loaded {len(test_normal_samples)} test-normal samples")

    # Run interactive test
    test_results = run_interactive_test(
        test_normal_samples,
        agent,
        max_samples=MAX_TEST_SAMPLES
    )

    evaluation_results = {
        'timestamp': timestamp,
        'config': {
            'max_test_samples': MAX_TEST_SAMPLES,
            'playbook_path': str(playbook_path),
            'request_dir': request_dir
        },
        'test_results': test_results
    }

    # Save results
    with open(results_file, 'w') as f:
        json.dump(evaluation_results, f, indent=2)

    print(f"\n✅ Results saved to: {results_file}")

    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    print("1. When you see a request file created in /tmp/appworld_requests/")
    print("2. Read the request file to see task details and bullets")
    print("3. Use the 'generate-appworld-code' Skill to generate code")
    print("4. Use create_response_file() helper to write response")
    print("   Example:")
    print("   from benchmarks.utils.claude_code_react_agent import create_response_file")
    print("   create_response_file(")
    print("       '/tmp/appworld_requests/response_turn_1.json',")
    print("       code='# Your generated code',")
    print("       reasoning='I applied the playbook strategies...'")
    print("   )")
    print("="*70)


if __name__ == "__main__":
    main()
