#!/usr/bin/env python3
"""
Standalone Skill Monitor for Interactive Protocol

Monitors /tmp/appworld_requests/ for request files and generates code responses.

This is a CODE GENERATION service only - it does NOT execute code.
Code execution happens in the real AppWorld environment via ClaudeCodeReActAgent.

Role:
- Reads request files with task instructions and playbook bullets
- Generates AppWorld Python code using app-specific patterns
- Writes response files containing ONLY the generated code
- ClaudeCodeReActAgent then executes that code in AppWorld and gets real TGC scores
"""

import json
import time
from pathlib import Path

REQUEST_DIR = Path("/tmp/appworld_requests")
CHECK_INTERVAL = 1  # seconds


def generate_spotify_code(instruction: str, strategies: list) -> str:
    """Generate Spotify-specific code."""
    instruction_lower = instruction.lower()

    # Detect task type
    if 'most-liked' in instruction_lower or 'most liked' in instruction_lower:
        aggregation = 'max'
        metric = 'likes'
    elif 'least-played' in instruction_lower or 'least played' in instruction_lower:
        aggregation = 'min'
        metric = 'play_count'
    elif 'most-played' in instruction_lower or 'most played' in instruction_lower:
        aggregation = 'max'
        metric = 'play_count'
    else:
        aggregation = 'max'
        metric = 'likes'

    # Detect source
    if 'playlist' in instruction_lower:
        source = 'playlists'
    elif 'album' in instruction_lower:
        source = 'albums'
    else:
        source = 'library'

    code = f'''# Spotify task: {instruction}
# Applying strategies: {", ".join(strategies) if strategies else "None"}

try:
    # Login to Spotify
    response = apis.spotify.login(username="user@example.com", password="password")
    token = response["access_token"]

    all_songs = []

    '''

    if source == 'playlists':
        code += '''    # Get all playlists
    playlists = apis.spotify.show_playlist_library(access_token=token)

    # Collect songs from all playlists
    for playlist in playlists:
        songs = apis.spotify.show_playlist_songs(
            access_token=token,
            playlist_id=playlist["id"]
        )
        all_songs.extend(songs)
'''
    elif source == 'albums':
        code += '''    # Get all albums
    albums = apis.spotify.show_album_library(access_token=token)

    # Collect songs from all albums
    for album in albums:
        songs = apis.spotify.show_album_songs(
            access_token=token,
            album_id=album["id"]
        )
        all_songs.extend(songs)
'''
    else:
        code += '''    # Get all songs from library
    all_songs = apis.spotify.show_song_library(access_token=token)
'''

    if aggregation == 'max':
        code += f'''
    # Find song with highest {metric}
    target_song = max(all_songs, key=lambda s: s.get("{metric}", 0))
    result = target_song["title"]
'''
    else:
        code += f'''
    # Find song with lowest {metric}
    target_song = min(all_songs, key=lambda s: s.get("{metric}", float('inf')))
    result = target_song["title"]
'''

    code += '''
    # Complete task
    apis.supervisor.complete_task()

except Exception as e:
    print(f"Error: {str(e)}")
    raise
'''

    return code


def generate_gmail_code(instruction: str, strategies: list) -> str:
    """Generate Gmail-specific code."""
    code = f'''# Gmail task: {instruction}
# Applying strategies: {", ".join(strategies) if strategies else "None"}

try:
    # Login to Gmail
    response = apis.gmail.login(username="user@example.com", password="password")
    token = response["access_token"]

    # Fetch emails
    emails = apis.gmail.fetch_emails(
        access_token=token,
        max_results=50,
        query="is:all"
    )

    # Process emails
    result = f"Found {{len(emails)}} emails"

    # Complete task
    apis.supervisor.complete_task()

except Exception as e:
    print(f"Error: {{str(e)}}")
    raise
'''
    return code


def generate_generic_code(instruction: str, app: str, strategies: list) -> str:
    """Generate generic fallback code."""
    code = f'''# Generic task: {instruction}
# App: {app}
# Applying strategies: {", ".join(strategies) if strategies else "None"}

try:
    # TODO: Implement task-specific logic
    result = "Task completed (generic implementation)"

    # Complete task
    apis.supervisor.complete_task()

except Exception as e:
    print(f"Error: {{str(e)}}")
    raise
'''
    return code


def generate_appworld_code(instruction: str, apps: list, strategies: list) -> str:
    """
    Generate AppWorld Python code for a task.

    Args:
        instruction: Task instruction
        apps: List of available apps (e.g., ['spotify', 'gmail'])
        strategies: List of strategy hints from playbook

    Returns:
        Python code string
    """
    # Determine primary app
    primary_app = apps[0] if apps and apps[0] != 'general' else None

    if not primary_app or primary_app == 'general':
        # Generic task - try to infer from instruction
        instruction_lower = instruction.lower()
        if 'spotify' in instruction_lower or 'song' in instruction_lower or 'playlist' in instruction_lower:
            primary_app = 'spotify'
        elif 'email' in instruction_lower or 'gmail' in instruction_lower:
            primary_app = 'gmail'

    # Generate app-specific code
    if primary_app == 'spotify':
        return generate_spotify_code(instruction, strategies)
    elif primary_app == 'gmail':
        return generate_gmail_code(instruction, strategies)
    else:
        # Generic fallback
        return generate_generic_code(instruction, primary_app or 'unknown', strategies)


def monitor_requests():
    """Monitor request directory and process new requests."""
    print("=" * 70)
    print("SKILL MONITOR: Interactive Protocol (Standalone)")
    print("=" * 70)
    print(f"Monitoring: {REQUEST_DIR}")
    print(f"Check interval: {CHECK_INTERVAL}s")
    print("=" * 70)
    print()

    # Track processed requests by (filename, timestamp) to handle file rewrites
    processed_requests = {}  # filename -> timestamp

    while True:
        try:
            # Find all request files
            request_files = list(REQUEST_DIR.glob("request_*.json"))

            for request_file in request_files:
                request_id = request_file.stem  # e.g., "request_turn_1"
                response_file = REQUEST_DIR / f"response_{request_id.split('_', 1)[1]}.json"

                # Skip if response already exists (prevents duplicate processing)
                if response_file.exists():
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

                # Extract strategies
                strategies = [b.get('title', '') for b in bullets if 'title' in b]

                # Generate code
                print(f"\n⚙️  Generating code...")

                try:
                    code = generate_appworld_code(instruction, apps, strategies)

                    print(f"✓ Generated {len(code.splitlines())} lines of code")
                    print(f"\nCode preview:")
                    print(code[:200] + "...")

                    # Write response (CODE ONLY - execution happens in AppWorld)
                    response_data = {
                        'code': code,
                        'reasoning': f"Generated code using {len(strategies)} playbook strategies",
                        'timestamp': time.time()
                    }

                    with open(response_file, 'w') as f:
                        json.dump(response_data, f, indent=2)

                    print(f"\n✅ Code response written to: {response_file.name}")
                    print(f"   (Code will be executed in real AppWorld by ClaudeCodeReActAgent)")

                except Exception as e:
                    print(f"❌ Error generating code: {e}")
                    import traceback
                    traceback.print_exc()

                    # Write error response
                    error_response = {
                        'code': f'# Code generation error: {str(e)}\nraise Exception("{str(e)}")',
                        'reasoning': f'Code generation failed: {str(e)}',
                        'timestamp': time.time()
                    }

                    with open(response_file, 'w') as f:
                        json.dump(error_response, f, indent=2)

                    print(f"⚠️  Error response written")

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


def main():
    """Main entry point."""
    # Ensure request directory exists
    REQUEST_DIR.mkdir(parents=True, exist_ok=True)

    print("\n🚀 Starting Standalone Skill Monitor...")
    print("   Code generation only - execution happens in AppWorld\n")

    monitor_requests()


if __name__ == '__main__':
    main()
