#!/usr/bin/env python3
"""
Interactive Protocol Skill Monitor

Monitors /tmp/appworld_requests/ for request files and generates responses using
the generate-appworld-code Skill.

This enables the AppWorldExecutor → Claude Code Skill → AppWorld pipeline.
"""

import json
import os
import time
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.claude_code_skill_invoker import invoke_skill


REQUEST_DIR = Path("/tmp/appworld_requests")
CHECK_INTERVAL = 2  # seconds


def monitor_requests():
    """Monitor request directory and process new requests."""
    print("=" * 70)
    print("SKILL MONITOR: Interactive Protocol")
    print("=" * 70)
    print(f"Monitoring: {REQUEST_DIR}")
    print(f"Check interval: {CHECK_INTERVAL}s")
    print(f"Skill: generate-appworld-code")
    print("=" * 70)
    print()

    processed_requests = set()

    while True:
        try:
            # Find all request files
            request_files = list(REQUEST_DIR.glob("request_*.json"))

            for request_file in request_files:
                request_id = request_file.stem  # e.g., "request_turn_1"
                response_file = REQUEST_DIR / f"response_{request_id.split('_', 1)[1]}.json"

                # Skip if already processed or response exists
                if request_id in processed_requests or response_file.exists():
                    continue

                print(f"\n{'='*70}")
                print(f"📥 NEW REQUEST: {request_file.name}")
                print(f"{'='*70}")

                # Read request
                try:
                    with open(request_file, 'r') as f:
                        request_data = json.load(f)
                except Exception as e:
                    print(f"❌ Error reading request: {e}")
                    continue

                # Extract task info
                instruction = request_data.get('instruction', 'Unknown task')
                apps = request_data.get('apps', [])
                bullets = request_data.get('bullets', [])
                turn = request_data.get('turn', 1)
                history = request_data.get('execution_history', [])

                print(f"\nTask: {instruction}")
                print(f"Apps: {apps}")
                print(f"Turn: {turn}")
                print(f"Bullets: {len(bullets)} guidance points")
                print(f"History: {len(history)} previous attempts")

                # Generate code using Skill
                print(f"\n⚙️  Invoking generate-appworld-code Skill...")

                try:
                    code = invoke_generate_appworld_code_skill(
                        instruction=instruction,
                        apps=apps,
                        bullets=bullets,
                        execution_history=history
                    )

                    print(f"✓ Generated {len(code.splitlines())} lines of code")

                    # Execute code in AppWorld
                    print(f"\n🚀 Executing in AppWorld...")
                    result = execute_in_appworld(code, instruction, apps)

                    print(f"📊 Result:")
                    print(f"   Success: {result['success']}")
                    print(f"   TGC: {result.get('tgc', 0.0):.2f}")
                    print(f"   SGC: {result.get('sgc', 0.0):.2f}")

                    # Write response
                    response_data = {
                        'code': code,
                        'success': result['success'],
                        'tgc': result.get('tgc', 0.0),
                        'sgc': result.get('sgc', 0.0),
                        'result': result.get('result', ''),
                        'execution_feedback': result.get('execution_feedback', {}),
                        'timestamp': time.time()
                    }

                    with open(response_file, 'w') as f:
                        json.dump(response_data, f, indent=2)

                    print(f"✅ Response written to: {response_file.name}")
                    processed_requests.add(request_id)

                except Exception as e:
                    print(f"❌ Error processing request: {e}")
                    import traceback
                    traceback.print_exc()

                    # Write error response
                    error_response = {
                        'code': '',
                        'success': False,
                        'tgc': 0.0,
                        'sgc': 0.0,
                        'result': f'Skill error: {str(e)}',
                        'execution_feedback': {'error': str(e)},
                        'timestamp': time.time()
                    }

                    with open(response_file, 'w') as f:
                        json.dump(error_response, f, indent=2)

                    print(f"⚠️  Error response written")
                    processed_requests.add(request_id)

            # Sleep before next check
            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n\n🛑 Skill monitor stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Monitor error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(CHECK_INTERVAL)


def invoke_generate_appworld_code_skill(instruction, apps, bullets, execution_history):
    """
    Invoke the generate-appworld-code Skill to generate Python code.

    Args:
        instruction: Task instruction
        apps: List of available apps
        bullets: List of playbook bullets
        execution_history: Previous execution attempts

    Returns:
        Generated Python code string
    """
    # Build skill prompt
    strategies = []
    for bullet in bullets:
        if 'title' in bullet:
            strategies.append(bullet['title'])

    # Format history for context
    history_context = ""
    if execution_history:
        history_context = "\n\n## Previous Attempts:\n"
        for i, attempt in enumerate(execution_history, 1):
            result = attempt.get('result', 'Unknown result')
            history_context += f"\nAttempt {i}: {result}"

    # Skill input
    skill_input = f"""# Task
{instruction}

## Available Apps
{', '.join(apps)}

## Strategies from Playbook
{chr(10).join(f'- {s}' for s in strategies)}

## Bullet Details
{json.dumps(bullets, indent=2)}
{history_context}

Generate Python code to solve this task using AppWorld APIs. Apply the strategies from the playbook bullets.
"""

    # Invoke skill using SlashCommand
    print(f"\n📝 Skill Input:")
    print(f"   Instruction: {instruction[:60]}...")
    print(f"   Apps: {apps}")
    print(f"   Strategies: {len(strategies)}")

    try:
        # Use invoke_skill helper
        code = invoke_skill("generate-appworld-code", skill_input)
        return code

    except Exception as e:
        print(f"❌ Skill invocation failed: {e}")
        # Fallback to basic code template
        return generate_fallback_code(instruction, apps)


def generate_fallback_code(instruction, apps):
    """Generate basic fallback code when skill fails."""
    return f"""# Task: {instruction}
# Apps: {', '.join(apps)}

# Fallback code - skill invocation failed
try:
    # TODO: Implement task logic
    result = "Task not implemented (skill error)"

    # Complete task
    apis.supervisor.complete_task()

except Exception as e:
    print(f"Error: {{str(e)}}")
    raise
"""


def execute_in_appworld(code, instruction, apps):
    """
    Execute generated code in AppWorld environment.

    Args:
        code: Python code to execute
        instruction: Task instruction
        apps: List of apps

    Returns:
        Dict with execution results
    """
    from appworld import Benchmark

    try:
        # Initialize AppWorld benchmark
        benchmark = Benchmark()

        # Create a temporary task for execution
        task = {
            'id': f'interactive_{int(time.time())}',
            'instruction': instruction,
            'apps': apps,
            'code': code
        }

        # Execute code
        result = benchmark.execute_code(code, task_id=task['id'])

        # Extract scores
        tgc = result.get('tgc', 0.0)
        sgc = result.get('sgc', 0.0)
        success = tgc >= 0.5 and sgc >= 0.5

        # Analyze errors if failed
        execution_feedback = {}
        if not success:
            execution_feedback = analyze_execution_errors(
                result=result,
                code=code,
                instruction=instruction,
                apps=apps
            )

        return {
            'success': success,
            'tgc': tgc,
            'sgc': sgc,
            'result': result.get('output', ''),
            'execution_feedback': execution_feedback
        }

    except Exception as e:
        # Return error result
        return {
            'success': False,
            'tgc': 0.0,
            'sgc': 0.0,
            'result': f'Execution error: {str(e)}',
            'execution_feedback': {
                'error_analysis': {
                    'error_type': 'execution_error',
                    'error_messages': [str(e)],
                    'failed_apis': [],
                    'missing_patterns': ['Execution failed'],
                    'suggested_fixes': ['Check code syntax and AppWorld API usage']
                }
            }
        }


def analyze_execution_errors(result, code, instruction, apps):
    """
    Analyze execution errors to provide rich error_analysis for Reflector.

    This is similar to AppWorldExecutor._analyze_execution_errors().
    """
    error_analysis = {
        'error_type': None,
        'error_messages': [],
        'failed_apis': [],
        'missing_patterns': [],
        'suggested_fixes': []
    }

    output = result.get('output', '')
    error_msg = result.get('error', '')

    # Combine error messages
    all_errors = []
    if error_msg:
        all_errors.append(error_msg)
    if 'error' in output.lower():
        all_errors.append(output)

    error_analysis['error_messages'] = all_errors

    # Detect error types
    error_text = ' '.join(all_errors).lower()

    # Authentication errors
    if 'access_token' in error_text or 'authentication' in error_text or 'login' in error_text:
        error_analysis['error_type'] = 'authentication_error'
        error_analysis['missing_patterns'].append('Always call login() first')
        error_analysis['suggested_fixes'].append(f'Add {apps[0]}.login() before API calls' if apps else 'Add login() call')

    # API misuse (wrong method names)
    elif 'attributeerror' in error_text or 'keyerror' in error_text or 'not found' in error_text:
        error_analysis['error_type'] = 'api_misuse'
        error_analysis['missing_patterns'].append('Need correct API method names')
        error_analysis['suggested_fixes'].append('Check AppWorld API documentation for correct method names')

    # Missing data (None errors)
    elif 'nonetype' in error_text or 'none has no attribute' in error_text:
        error_analysis['error_type'] = 'missing_data'
        error_analysis['missing_patterns'].append('Check response structure before accessing fields')
        error_analysis['suggested_fixes'].append('Verify API response contains expected data')

    # Logic error (tests fail without execution errors)
    elif result.get('tgc', 0) < 1.0:
        error_analysis['error_type'] = 'logic_error'
        error_analysis['missing_patterns'].append('Task logic needs refinement')
        error_analysis['suggested_fixes'].append('Review task requirements and API usage')

    # Default
    else:
        error_analysis['error_type'] = 'wrong_source'
        error_analysis['missing_patterns'].append('Check API source and logic')

    # Check for missing login in code
    if apps:
        for app in apps:
            if f'{app}.login(' not in code:
                error_analysis['missing_patterns'].append(f'Missing login() call for {app}')
                error_analysis['failed_apis'].append(f'{app}.login')

    return {'error_analysis': error_analysis}


def main():
    """Main entry point."""
    # Ensure request directory exists
    REQUEST_DIR.mkdir(parents=True, exist_ok=True)

    print("\n🚀 Starting Skill Monitor for Interactive Protocol...")
    monitor_requests()


if __name__ == '__main__':
    main()
