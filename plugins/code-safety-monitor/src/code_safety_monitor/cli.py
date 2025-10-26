#!/usr/bin/env python3
"""
CLI interface for Code Safety Monitor.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from .monitor import create_monitor
from .utils import format_suspicion_report, setup_api_key


def scan_command(args):
    """Scan a code file for backdoors."""
    # Setup API key
    setup_api_key(args.api_key)

    # Load monitor
    model_path = Path(args.model_path) if args.model_path else None
    monitor = create_monitor(
        model=args.model,
        model_path=model_path
    )

    # Read code
    code_path = Path(args.file_path)
    if not code_path.exists():
        print(f"Error: File not found: {code_path}")
        sys.exit(1)

    code = code_path.read_text()

    # Scan
    score, reasoning = monitor.scan_code(
        code=code,
        task_description=args.task or "General programming task"
    )

    # Format report
    report = format_suspicion_report(
        score,
        reasoning,
        threshold=args.threshold
    )

    print(report)

    # Exit code based on threshold
    if score >= args.threshold:
        sys.exit(1)  # Flagged
    else:
        sys.exit(0)  # Safe


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Code Safety Monitor - DSPy-powered backdoor detection"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan code file")
    scan_parser.add_argument("file_path", help="Path to code file to scan")
    scan_parser.add_argument(
        "--task",
        default=None,
        help="Task description (default: General programming task)"
    )
    scan_parser.add_argument(
        "--threshold",
        type=int,
        default=50,
        help="Suspicion threshold for flagging (default: 50)"
    )
    scan_parser.add_argument(
        "--model",
        default="openai/gpt-4o-mini",
        help="Model to use (default: gpt-4o-mini)"
    )
    scan_parser.add_argument(
        "--model-path",
        default=None,
        help="Path to optimized monitor model (optional)"
    )
    scan_parser.add_argument(
        "--api-key",
        default=None,
        help="OpenAI API key (or set OPENAI_API_KEY env var)"
    )
    scan_parser.set_defaults(func=scan_command)

    # Parse and execute
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
