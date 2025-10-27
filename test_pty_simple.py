#!/usr/bin/env python3
"""
Simple test of PTY-based Claude CLI invocation
"""
import subprocess
import pty
import os
import select
import time

def run_claude_with_pty(prompt):
    """Run Claude CLI using PTY"""
    master_fd, slave_fd = pty.openpty()

    try:
        proc = subprocess.Popen(
            ['claude', '--print', '--output-format', 'text'],
            stdin=subprocess.PIPE,
            stdout=slave_fd,
            stderr=subprocess.PIPE,
            text=True
        )

        if proc.stdin:
            proc.stdin.write(prompt)
            proc.stdin.close()

        os.close(slave_fd)

        output_chunks = []
        start_time = time.time()
        timeout = 60

        while True:
            remaining = timeout - (time.time() - start_time)
            if remaining <= 0:
                proc.kill()
                raise RuntimeError("Timeout")

            read_ready, _, _ = select.select([master_fd], [], [], min(1.0, remaining))

            if master_fd in read_ready:
                data = os.read(master_fd, 4096)
                if not data:
                    if proc.poll() is not None:
                        break
                    continue
                output_chunks.append(data.decode('utf-8', errors='ignore'))

            if proc.poll() is not None and not read_ready:
                break

        stdout_text = ''.join(output_chunks)
        stderr_text = proc.stderr.read().strip() if proc.stderr else ""

        retcode = proc.wait(timeout=5)

        return stdout_text, stderr_text, retcode

    finally:
        try:
            os.close(master_fd)
        except:
            pass
        try:
            os.close(slave_fd)
        except:
            pass


def main():
    prompt = """Generate a simple JSON object with this exact structure:
{
  "delta": {
    "new_bullets": [],
    "counters": {"test_counter": 1}
  }
}

Reply ONLY with valid JSON, no explanation."""

    print("Testing PTY-based Claude CLI invocation")
    print("=" * 60)
    print(f"Prompt ({len(prompt)} chars):")
    print(prompt)
    print("=" * 60)

    print("\nRunning Claude CLI with PTY...")
    start = time.time()

    try:
        stdout, stderr, retcode = run_claude_with_pty(prompt)
        elapsed = time.time() - start

        print(f"\n✅ Completed in {elapsed:.2f}s")
        print(f"Exit code: {retcode}")
        print(f"Stdout length: {len(stdout)} chars")
        print(f"Stderr length: {len(stderr)} chars")

        if stderr:
            print(f"\nStderr:\n{stderr[:500]}")

        if stdout:
            print(f"\nStdout:")
            print("-" * 40)
            print(stdout[:1000])
            print("-" * 40)

            # Try to find JSON in response
            import json
            import re

            # Look for JSON pattern
            json_match = re.search(r'\{[^}]*"delta"[^}]*\}', stdout, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    print(f"\n✅ Found valid JSON!")
                    print(json.dumps(result, indent=2))
                except:
                    print("\n⚠️ Found JSON-like content but couldn't parse")
            else:
                print("\n⚠️ No JSON found in response")
        else:
            print("\n❌ Empty stdout")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()