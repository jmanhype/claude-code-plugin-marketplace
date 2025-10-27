---
name: generate-appworld-code
description: Generate Python code to solve AppWorld agent tasks using playbook bullet guidance. Use when the AppWorld executor needs executable Python code for tasks involving Spotify, Venmo, Gmail, Calendar, Contacts, or other AppWorld APIs.
allowed-tools: Read
---

# Generate AppWorld Code

Generate executable Python code for AppWorld agent tasks, applying learned strategies from the ACE playbook.

## Purpose

When the AppWorld executor encounters a task, it calls this Skill with:
- Task instruction (natural language)
- Available apps (e.g., ['spotify', 'venmo'])
- Playbook bullets (learned strategies to apply)

You generate Python code that:
1. Solves the task using AppWorld APIs
2. Applies bullet guidance strategies
3. Handles errors gracefully
4. Calls `apis.supervisor.complete_task()` when done

## Input Format

```json
{
  "instruction": "What is the title of the most-liked song in my Spotify playlists",
  "apps": ["spotify"],
  "strategies": [
    "Always login before API calls",
    "Handle pagination for large result sets"
  ],
  "bullets": [
    {
      "id": "bullet-xxx",
      "title": "Spotify login pattern",
      "content": "Login to Spotify using apis.spotify.login() with credentials..."
    }
  ]
}
```

## AppWorld API Patterns

### Spotify
```python
# Login
response = apis.spotify.login(username="user@example.com", password="password")
token = response["access_token"]

# Get playlists
playlists = apis.spotify.show_playlist_library(access_token=token)

# Get songs in playlist
songs = apis.spotify.show_playlist_songs(
    access_token=token,
    playlist_id=playlists[0]["id"]
)
```

### Venmo
```python
# Login
response = apis.venmo.login(username="user@example.com", password="password")
token = response["access_token"]

# Get friends
friends = apis.venmo.show_friends(access_token=token)

# Send payment
apis.venmo.send_payment(
    access_token=token,
    recipient_id=friend["id"],
    amount=10.00,
    note="Payment note"
)
```

### Gmail
```python
# Login
response = apis.gmail.login(username="user@example.com", password="password")
token = response["access_token"]

# Fetch emails
emails = apis.gmail.fetch_emails(
    access_token=token,
    max_results=10,
    query="is:unread"
)

# Send email
apis.gmail.send_email(
    access_token=token,
    to="recipient@example.com",
    subject="Subject",
    body="Email body"
)
```

### Contacts
```python
# Get contacts
contacts = apis.contacts.show_contacts()

# Add contact
apis.contacts.add_contact(
    name="John Doe",
    email="john@example.com",
    phone="+1234567890"
)
```

### Calendar
```python
# Get events
events = apis.calendar.show_events(
    start_date="2025-01-01",
    end_date="2025-12-31"
)

# Create event
apis.calendar.create_event(
    title="Meeting",
    start_time="2025-10-26T14:00:00",
    end_time="2025-10-26T15:00:00"
)
```

## Code Generation Rules

1. **Always complete task**: Call `apis.supervisor.complete_task()` at the end
2. **Apply bullet strategies**: Use patterns from playbook bullets
3. **Handle errors**: Use try/except for API calls
4. **Be specific**: Don't use placeholders - generate actual implementations
5. **No explanations**: Return ONLY executable Python code

## Example Generation

**Input**:
```json
{
  "instruction": "Send an email to john@example.com saying hello",
  "apps": ["gmail"],
  "strategies": ["Login before API calls", "Validate email addresses"],
  "bullets": [...]
}
```

**Output**:
```python
# Gmail task: Send email to john@example.com
# Applying strategies: Login before API calls, Validate email addresses

try:
    # Login to Gmail
    response = apis.gmail.login(username="user@example.com", password="password")
    token = response["access_token"]

    # Validate recipient
    recipient = "john@example.com"
    if "@" not in recipient:
        raise ValueError(f"Invalid email: {recipient}")

    # Send email
    apis.gmail.send_email(
        access_token=token,
        to=recipient,
        subject="Hello",
        body="Hello from AppWorld!"
    )

    # Complete task
    apis.supervisor.complete_task()

except Exception as e:
    print(f"Error: {str(e)}")
    raise
```

## Credentials

AppWorld provides test credentials automatically. Use these common patterns:
- `username="user@example.com"`
- `password="password"`
- Tokens are returned from login APIs

## Common Patterns from Playbook

### Pattern: Friend Management (Venmo/Contacts)
```python
# Get current friends
current_friends = apis.venmo.show_friends(access_token=token)
current_ids = {f["id"] for f in current_friends}

# Get target friends (from contacts)
target_contacts = apis.contacts.show_contacts()
target_ids = {c["id"] for c in target_contacts if c.get("venmo_id")}

# Add missing
for target_id in target_ids - current_ids:
    apis.venmo.add_friend(access_token=token, user_id=target_id)

# Remove extra
for current_id in current_ids - target_ids:
    apis.venmo.remove_friend(access_token=token, user_id=current_id)
```

### Pattern: Aggregation (Spotify/Media)
```python
# Get all playlists
playlists = apis.spotify.show_playlist_library(access_token=token)

all_songs = []
for playlist in playlists:
    songs = apis.spotify.show_playlist_songs(
        access_token=token,
        playlist_id=playlist["id"]
    )
    all_songs.extend(songs)

# Find most-liked
most_liked = max(all_songs, key=lambda s: s.get("likes", 0))
result = most_liked["title"]
```

## Response Format

Return Python code as plain text (no markdown formatting, no explanations).

The code should be immediately executable in the AppWorld environment.
