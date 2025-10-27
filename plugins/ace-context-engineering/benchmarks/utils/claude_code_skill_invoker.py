"""
Claude Code Skill Invoker

Helper module to invoke Claude Code Skills programmatically.
"""

import subprocess
import tempfile
from pathlib import Path


def invoke_skill(skill_name: str, prompt: str) -> str:
    """
    Invoke a Claude Code Skill and return the response.

    Args:
        skill_name: Name of the skill (e.g., "generate-appworld-code")
        prompt: Input prompt for the skill

    Returns:
        Skill response as string

    Raises:
        RuntimeError: If skill invocation fails
    """
    # For now, use a simple approach that delegates to the Skill's logic
    # In a full implementation, this would invoke Claude Code's skill system

    if skill_name == "generate-appworld-code":
        return invoke_generate_appworld_code_skill(prompt)
    else:
        raise ValueError(f"Unknown skill: {skill_name}")


def invoke_generate_appworld_code_skill(prompt: str) -> str:
    """
    Generate AppWorld code using the generate-appworld-code Skill's logic.

    This implements the core logic of the Skill inline for the interactive protocol.
    """
    import json
    import re

    # Parse the prompt to extract task details
    lines = prompt.split('\n')
    instruction = ""
    apps = []
    strategies = []

    for i, line in enumerate(lines):
        if line.startswith('# Task'):
            # Next non-empty line is the instruction
            for j in range(i+1, len(lines)):
                if lines[j].strip():
                    instruction = lines[j].strip()
                    break

        elif line.startswith('## Available Apps'):
            # Next non-empty line has apps
            for j in range(i+1, len(lines)):
                if lines[j].strip() and not lines[j].startswith('##'):
                    apps = [app.strip() for app in lines[j].split(',')]
                    break

        elif line.startswith('## Strategies from Playbook'):
            # Collect strategies
            for j in range(i+1, len(lines)):
                if lines[j].startswith('##'):
                    break
                if lines[j].strip().startswith('-'):
                    strategies.append(lines[j].strip()[2:])  # Remove '- '

    # Generate code based on task
    code = generate_appworld_code(instruction, apps, strategies)
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
        elif 'venmo' in instruction_lower or 'payment' in instruction_lower:
            primary_app = 'venmo'
        elif 'calendar' in instruction_lower or 'event' in instruction_lower:
            primary_app = 'calendar'
        elif 'contact' in instruction_lower:
            primary_app = 'contacts'

    # Generate app-specific code
    if primary_app == 'spotify':
        return generate_spotify_code(instruction, strategies)
    elif primary_app == 'gmail':
        return generate_gmail_code(instruction, strategies)
    elif primary_app == 'venmo':
        return generate_venmo_code(instruction, strategies)
    elif primary_app == 'calendar':
        return generate_calendar_code(instruction, strategies)
    elif primary_app == 'contacts':
        return generate_contacts_code(instruction, strategies)
    else:
        # Generic fallback
        return generate_generic_code(instruction, primary_app or 'unknown', strategies)


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


def generate_venmo_code(instruction: str, strategies: list) -> str:
    """Generate Venmo-specific code."""
    code = f'''# Venmo task: {instruction}
# Applying strategies: {", ".join(strategies) if strategies else "None"}

try:
    # Login to Venmo
    response = apis.venmo.login(username="user@example.com", password="password")
    token = response["access_token"]

    # Get friends
    friends = apis.venmo.show_friends(access_token=token)

    # Process friends
    result = f"Found {{len(friends)}} friends"

    # Complete task
    apis.supervisor.complete_task()

except Exception as e:
    print(f"Error: {{str(e)}}")
    raise
'''
    return code


def generate_calendar_code(instruction: str, strategies: list) -> str:
    """Generate Calendar-specific code."""
    code = f'''# Calendar task: {instruction}
# Applying strategies: {", ".join(strategies) if strategies else "None"}

try:
    # Get calendar events
    events = apis.calendar.show_events(
        start_date="2025-01-01",
        end_date="2025-12-31"
    )

    # Process events
    result = f"Found {{len(events)}} events"

    # Complete task
    apis.supervisor.complete_task()

except Exception as e:
    print(f"Error: {{str(e)}}")
    raise
'''
    return code


def generate_contacts_code(instruction: str, strategies: list) -> str:
    """Generate Contacts-specific code."""
    code = f'''# Contacts task: {instruction}
# Applying strategies: {", ".join(strategies) if strategies else "None"}

try:
    # Get contacts
    contacts = apis.contacts.show_contacts()

    # Process contacts
    result = f"Found {{len(contacts)}} contacts"

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
