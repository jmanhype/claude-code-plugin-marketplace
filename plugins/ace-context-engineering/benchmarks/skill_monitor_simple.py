#!/usr/bin/env python3
"""
Simple Interactive Protocol Skill Monitor

Monitors /tmp/appworld_requests/ for request files and generates code responses.
This simplified version demonstrates the interactive protocol without full AppWorld execution.
"""

import json
import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.claude_code_skill_invoker import invoke_generate_appworld_code_skill


REQUEST_DIR = Path("/tmp/appworld_requests")
CHECK_INTERVAL = 1  # seconds


def monitor_requests():
    """Monitor request directory and process new requests."""
    print("=" * 70)
    print("SKILL MONITOR: Interactive Protocol (Simple)")
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

                # Build prompt for skill
                strategies = [b.get('title', '') for b in bullets if 'title' in b]

                history_context = ""
                if history:
                    history_context = "\n\n## Previous Attempts:\n"
                    for i, attempt in enumerate(history, 1):
                        result = attempt.get('result', 'Unknown result')
                        history_context += f"\nAttempt {i}: {result}"

                prompt = f"""# Task
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

                # Generate code using Skill
                print(f"\n⚙️  Invoking generate-appworld-code Skill...")

                try:
                    code = invoke_generate_appworld_code_skill(prompt)

                    print(f"✓ Generated {len(code.splitlines())} lines of code")
                    print(f"\nCode preview:")
                    print(code[:200] + "...")

                    # Simulate execution with mock results
                    # In a full implementation, this would execute in AppWorld
                    result = simulate_execution(code, instruction, apps, turn)

                    print(f"\n📊 Simulated Result:")
                    print(f"   Success: {result['success']}")
                    print(f"   TGC: {result.get('tgc', 0.0):.2f}")
                    print(f"   SGC: {result.get('sgc', 0.0):.2f}")

                    if 'execution_feedback' in result and 'error_analysis' in result['execution_feedback']:
                        ea = result['execution_feedback']['error_analysis']
                        print(f"\n🔍 Error Analysis:")
                        print(f"   Type: {ea.get('error_type', 'None')}")
                        print(f"   Messages: {len(ea.get('error_messages', []))}")
                        print(f"   Missing patterns: {len(ea.get('missing_patterns', []))}")

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

                    print(f"\n✅ Response written to: {response_file.name}")
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


def simulate_execution(code, instruction, apps, turn):
    """
    Simulate code execution with mock results.

    This demonstrates the rich error_analysis that AppWorldExecutor provides.
    In a full implementation, this would execute in AppWorld and analyze real errors.
    """
    # Simulate different outcomes based on turn (demonstrating learning)
    if turn == 1:
        # First attempt - authentication error
        return {
            'success': False,
            'tgc': 0.0,
            'sgc': 0.0,
            'result': 'Authentication error: Missing access_token',
            'execution_feedback': {
                'error_analysis': {
                    'error_type': 'authentication_error',
                    'error_messages': ['Missing access_token in request'],
                    'failed_apis': [f'{apps[0]}.search_tracks' if apps and apps[0] != 'general' else 'unknown.api'],
                    'missing_patterns': ['Always call login() first'],
                    'suggested_fixes': [f'Add {apps[0]}.login() before API calls' if apps and apps[0] != 'general' else 'Add login() call']
                }
            }
        }
    elif turn == 2:
        # Second attempt - API misuse
        return {
            'success': False,
            'tgc': 0.25,
            'sgc': 0.25,
            'result': 'TGC: 0.25, SGC: 0.25 (AttributeError: get_playlists not found)',
            'execution_feedback': {
                'error_analysis': {
                    'error_type': 'api_misuse',
                    'error_messages': ["AttributeError: 'spotify' object has no attribute 'get_playlists'"],
                    'failed_apis': ['spotify.get_playlists'],
                    'missing_patterns': ['Use correct method names: show_playlist_library instead of get_playlists'],
                    'suggested_fixes': ['Use show_* methods for Spotify, not get_/fetch_']
                }
            }
        }
    else:
        # Third attempt - success or partial success
        return {
            'success': turn > 2,  # Success on turn 3+
            'tgc': 0.75 if turn == 3 else 1.0,
            'sgc': 0.75 if turn == 3 else 1.0,
            'result': f'TGC: {0.75 if turn == 3 else 1.0:.2f}, SGC: {0.75 if turn == 3 else 1.0:.2f}',
            'execution_feedback': {
                'error_analysis': {
                    'error_type': 'logic_error' if turn == 3 else None,
                    'error_messages': [] if turn > 3 else ['Test 2 failed: Incorrect song title'],
                    'failed_apis': [],
                    'missing_patterns': [] if turn > 3 else ['Need to check all playlists, not just first one'],
                    'suggested_fixes': [] if turn > 3 else ['Iterate through all playlists to find most-liked song']
                }
            }
        }


def main():
    """Main entry point."""
    # Ensure request directory exists
    REQUEST_DIR.mkdir(parents=True, exist_ok=True)

    print("\n🚀 Starting Skill Monitor (Simple) for Interactive Protocol...")
    print("   This version simulates execution to demonstrate Reflector integration\n")

    monitor_requests()


if __name__ == '__main__':
    main()
