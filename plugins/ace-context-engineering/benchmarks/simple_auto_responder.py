#!/usr/bin/env python3
"""
Simple polling-based auto-responder for AppWorld requests.
Polls /tmp/appworld_requests/ every second for new request files.
"""

import json
import time
from pathlib import Path

def generate_baseline_code(instruction, apps):
    """Generate baseline code based on task."""
    code_lines = [f"# Baseline code: {instruction[:60]}..."]
    code_lines.append("")

    # Login to all apps
    for app in apps:
        code_lines.append(f"# Login to {app}")
        code_lines.append(f"{app}_response = apis.{app}.login()")
        code_lines.append(f"{app}_token = {app}_response.get('access_token')")
        code_lines.append("")

    # App-specific patterns
    if 'venmo' in apps and 'phone' in apps:
        code_lines.extend([
            "# Get Venmo friends",
            "venmo_friends_response = apis.venmo.search_friends(",
            "    access_token=venmo_token, query='', page_limit=20",
            ")",
            "current_venmo_emails = set()",
            "for friend in venmo_friends_response.get('results', []):",
            "    if 'email' in friend:",
            "        current_venmo_emails.add(friend['email'])",
            "",
            "# Get phone contacts",
            "phone_contacts_response = apis.phone.search_contacts(",
            "    access_token=phone_token, query='', page_limit=20",
            ")",
            "phone_emails = set()",
            "for contact in phone_contacts_response.get('results', []):",
            "    if 'email' in contact:",
            "        phone_emails.add(contact['email'])",
            "",
            "# Sync",
            "emails_to_add = phone_emails - current_venmo_emails",
            "emails_to_remove = current_venmo_emails - phone_emails",
            "",
            "for email in emails_to_add:",
            "    try:",
            "        apis.venmo.add_friend(user_email=email, access_token=venmo_token)",
            "    except:",
            "        pass",
            "",
            "for email in emails_to_remove:",
            "    try:",
            "        apis.venmo.remove_friend(user_email=email, access_token=venmo_token)",
            "    except:",
            "        pass",
        ])
    else:
        code_lines.append("# Generic baseline")
        code_lines.append("pass")

    code_lines.append("")
    code_lines.append("# Complete task")
    code_lines.append("apis.supervisor.complete_task()")

    return "\n".join(code_lines)

def main():
    request_dir = Path("/tmp/appworld_requests")
    processed = set()

    print("="*70)
    print("SIMPLE AUTO-RESPONDER")
    print("="*70)
    print(f"Polling: {request_dir}")
    print("Press Ctrl+C to stop")
    print("="*70)

    try:
        while True:
            # Look for new request files
            for request_file in request_dir.glob("request_turn_*.json"):
                if request_file in processed:
                    continue

                # Check if response already exists
                turn = request_file.stem.split("_")[-1]
                response_file = request_dir / f"response_turn_{turn}.json"
                if response_file.exists():
                    processed.add(request_file)
                    continue

                # Process request
                try:
                    with open(request_file) as f:
                        request = json.load(f)

                    instruction = request['instruction']
                    apps = request['apps']
                    turn_num = request['turn']

                    print(f"\n🔔 Request: Turn {turn_num}")
                    print(f"   Task: {instruction[:60]}...")
                    print(f"   Apps: {', '.join(apps)}")

                    # Generate code
                    code = generate_baseline_code(instruction, apps)

                    # Write response
                    response = {
                        "code": code,
                        "reasoning": f"Auto-generated baseline (turn {turn_num})",
                        "timestamp": time.time()
                    }

                    with open(response_file, 'w') as f:
                        json.dump(response, f, indent=2)

                    print(f"   ✅ Response written!")
                    processed.add(request_file)

                except Exception as e:
                    print(f"   ❌ Error: {e}")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping...")
        print("✅ Auto-responder stopped")

if __name__ == "__main__":
    main()
