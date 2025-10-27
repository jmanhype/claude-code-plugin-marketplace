#!/usr/bin/env python3
"""
Quick test to verify AppWorldExecutor integration.
"""
import sys
from pathlib import Path

# Add AppWorld venv to path
appworld_path = Path("/tmp/appworld/venv_appworld/lib/python3.11/site-packages")
if str(appworld_path) not in sys.path and appworld_path.exists():
    sys.path.insert(0, str(appworld_path))

print("Testing AppWorldExecutor import...")

try:
    from utils.appworld_executor import create_appworld_executor, APPWORLD_AVAILABLE
    print(f"✓ AppWorldExecutor available: {APPWORLD_AVAILABLE}")

    if APPWORLD_AVAILABLE:
        playbook_path = Path(__file__).parent.parent / "skills" / "playbook.json"
        print(f"\nCreating executor with playbook: {playbook_path}")

        executor = create_appworld_executor(
            playbook_path=str(playbook_path),
            request_dir="/tmp/appworld_requests",
            max_turns=3,
            timeout_per_turn=300
        )

        print(f"✓ Created AppWorldExecutor: {type(executor)}")
        print(f"✓ Executor agent: {type(executor.agent)}")
        print(f"\n✅ AppWorldExecutor integration working!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
