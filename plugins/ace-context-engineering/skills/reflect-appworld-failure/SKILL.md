---
name: reflect-appworld-failure
description: Analyze AppWorld task failures to extract specific API patterns and generate actionable playbook bullets with concrete code examples
allowed-tools: Read
---

# Reflect on AppWorld Failure

Analyze failed AppWorld tasks to extract specific, actionable learnings that can be added to the playbook.

## Purpose

When an AppWorld task fails, the Reflector calls this Skill with error details and failed code. You analyze the failure semantically and generate a high-quality bullet with:
1. Specific title describing the pattern
2. Detailed content with working code examples
3. Relevant tags for retrieval
4. Appropriate confidence level

## Input Format

The input will be a text description with sections:

```
# Task
<task instruction>

## Apps
<comma-separated list of apps used>

## Error Type
<error_type: api_misuse, logic_error, timeout, etc.>

## Error Messages
<list of error messages from execution>

## Failed Code Snippet
<relevant code that failed>

## Missing Patterns (from heuristics)
<list of patterns the old system identified>

## Suggested Fixes (from heuristics)
<list of fix suggestions>
```

## Your Analysis Process

1. **Identify Root Cause**: What was the fundamental mistake?
   - Wrong API method name?
   - Missing authentication?
   - Incorrect data structure access?
   - Logic error?

2. **Extract Pattern**: What general pattern does this represent?
   - Is this specific to one app or applies to multiple?
   - Is this about API order (login first)?
   - Is this about method naming conventions?
   - Is this about data validation?

3. **Generate Concrete Example**: Create working code that demonstrates the CORRECT pattern

4. **Write Actionable Bullet**: Make it specific enough that the Generator can apply it

## Output Format

Return a JSON object with this structure:

```json
{
  "bullet": {
    "id": "bullet-YYYY-MM-DD-HHMMSS",
    "title": "<Specific pattern title>",
    "content": "<Detailed explanation with working code example>",
    "tags": ["app.<app_name>", "<error_category>", "<pattern_type>"],
    "evidence": [
      {
        "type": "execution",
        "ref": "<task_id>",
        "note": "<brief note about failure>"
      }
    ],
    "confidence": "high|medium|low",
    "scope": "app|global"
  }
}
```

## Bullet Quality Guidelines

### GOOD Bullets (Specific and Actionable)

**Title**: "Spotify: Use show_playlist_songs() not get_tracks()"
**Content**: "Spotify API uses show_playlist_songs(access_token, playlist_id) to retrieve tracks. The method get_tracks() does not exist. Example: `songs = apis.spotify.show_playlist_songs(access_token=token, playlist_id=playlist['id'])`"
**Tags**: ["app.spotify", "api_misuse", "method_names", "playlists"]

**Title**: "Venmo: Call login() before search_transactions()"
**Content**: "Venmo API requires authentication token for all operations. Always call venmo.login() first to get access_token, then pass it to other methods. Example: `response = apis.venmo.login(username='user', password='pass'); token = response['access_token']; results = apis.venmo.search_transactions(access_token=token, query={'friend': 'Alice'})`"
**Tags**: ["app.venmo", "authentication", "api_order", "search"]

### BAD Bullets (Too Generic)

**Title**: "Verify venmo API logic and requirements"
**Content**: "When implementing venmo operations: Check task logic and requirements; Missing login() call for venmo"
**Tags**: ["logic", "debugging", "api", "app.venmo"]

**Why Bad**: No concrete code example, vague guidance, doesn't teach the specific pattern

## Example Analysis

### Input:
```
# Task
What is the title of the most-liked song in my Spotify playlists

## Apps
spotify

## Error Type
api_misuse

## Error Messages
AttributeError: 'Spotify' object has no attribute 'get_tracks'

## Failed Code Snippet
songs = spotify.get_tracks(playlist_id=pid)

## Missing Patterns
- Use correct Spotify API methods

## Suggested Fixes
- Check Spotify API documentation for available methods
```

### Your Analysis:

1. **Root Cause**: Code used non-existent method `get_tracks()` instead of correct `show_playlist_songs()`

2. **Pattern**: Spotify uses `show_*` naming convention for retrieval methods

3. **Scope**: App-specific (Spotify)

### Output:
```json
{
  "bullet": {
    "id": "bullet-2025-10-27-123456",
    "title": "Spotify: Use show_playlist_songs() to get tracks from playlist",
    "content": "To retrieve songs from a Spotify playlist, use show_playlist_songs(access_token, playlist_id). Don't use get_tracks() - it doesn't exist. Example: `token = apis.spotify.login()['access_token']; playlists = apis.spotify.show_playlist_library(access_token=token); songs = apis.spotify.show_playlist_songs(access_token=token, playlist_id=playlists[0]['id']); most_liked = max(songs, key=lambda s: s['likes'])`",
    "tags": ["app.spotify", "api_misuse", "method_names", "playlists", "retrieval"],
    "evidence": [
      {
        "type": "execution",
        "ref": "spotify_task_001",
        "note": "AttributeError: 'Spotify' object has no attribute 'get_tracks'"
      }
    ],
    "confidence": "high",
    "scope": "app"
  }
}
```

## Common AppWorld Patterns to Look For

### Authentication Order
- Most apps require login() first to get access_token
- Token must be passed to subsequent API calls

### Method Naming Conventions
- Spotify: `show_*` for retrieval (show_playlist_songs, show_album_library)
- Venmo: `show_friends`, `send_payment`, `search_transactions`
- Gmail: `fetch_emails`, `send_email`
- Contacts: `show_contacts`, `add_contact`
- Calendar: `show_events`, `create_event`

### Data Structure Access
- API responses may have nested structures
- Always check if keys exist before accessing
- Use `.get()` with defaults for safety

### Aggregation Patterns
- To find "most-liked song in playlists": Get all playlists → Get songs from each → Find max by likes
- To find "most expensive transaction": Get all transactions → Find max by amount

### Task Completion
- ALWAYS call `apis.supervisor.complete_task()` at the end
- This signals successful completion to test framework

## Important Rules

1. **Be Specific**: Include actual method names, parameter names, and code examples
2. **Be Actionable**: The Generator should know exactly what to do after reading your bullet
3. **Include Working Code**: Show a complete example that demonstrates the correct pattern
4. **Tag Appropriately**: Use `app.<app_name>` for app-specific bullets, plus semantic tags
5. **Set Confidence**: "high" for clear patterns, "medium" for uncertain, "low" for speculative
6. **Return ONLY JSON**: No explanations, no markdown formatting outside the JSON

## Response Format

Return the JSON object as plain text. Make sure it's valid JSON that can be parsed directly.
