#!/usr/bin/env python3
"""
Plugin Validator
=================

Validates all plugins against schema and enforces security requirements:
1. Schema compliance (plugin.json structure)
2. Remote sources must be pinned to commit SHAs (not /main/)
3. Remote sources should have integrity (sha256) hashes
4. Permissions must be declared
5. Trading plugins require risk config

Exit codes:
- 0: All validations passed
- 1: One or more validations failed
"""

import json
import hashlib
import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple


# ANSI color codes for output
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load JSON schema."""
    with open(schema_path) as f:
        return json.load(f)


def load_plugin(plugin_path: Path) -> Tuple[str, Dict[str, Any]]:
    """Load plugin.json and return (plugin_name, data)."""
    with open(plugin_path) as f:
        data = json.load(f)
    return plugin_path.parent.name, data


def validate_schema(plugin_name: str, data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate plugin data against schema.
    Returns list of error messages (empty if valid).
    """
    try:
        import jsonschema
        jsonschema.validate(data, schema)
        return []
    except jsonschema.ValidationError as e:
        return [f"Schema validation failed: {e.message}"]
    except ImportError:
        return ["jsonschema library not installed (run: pip install jsonschema)"]


def check_remote_sources(plugin_name: str, data: Dict[str, Any]) -> List[str]:
    """
    Check that remote sources are pinned and have integrity hashes.

    Rules:
    - URLs with /main/ must be changed to commit SHA URLs (@<sha>)
    - Remote sources should have integrity field with sha256 hash
    """
    errors = []
    warnings = []

    # Check all blocks that may have remote sources
    for block_name in ("agents", "hooks", "commands", "workflows", "mcp", "helpers"):
        items = data.get(block_name, [])

        for item in items:
            source = item.get("source", "")
            item_name = item.get("name", "unnamed")

            # Skip local paths
            if not source.startswith("http"):
                continue

            # Check 1: Must not use /main/ branch
            if "/main/" in source or "/master/" in source:
                errors.append(
                    f"[{block_name}:{item_name}] Remote source uses /main/ or /master/ — must pin to commit SHA"
                )
                continue

            # Check 2: Should have commit SHA in URL (e.g., @<sha> or /<40-char-hex>/)
            has_commit_ref = bool(
                re.search(r"@[0-9a-f]{7,40}", source) or
                re.search(r"/[0-9a-f]{40}/", source)
            )

            if not has_commit_ref:
                errors.append(
                    f"[{block_name}:{item_name}] Remote source missing commit SHA in URL: {source}"
                )

            # Check 3: Should have integrity hash
            integrity = item.get("integrity")
            if not integrity:
                warnings.append(
                    f"[{block_name}:{item_name}] Remote source missing 'integrity' (sha256) field"
                )
            elif not re.match(r"^[a-f0-9]{64}$", integrity):
                errors.append(
                    f"[{block_name}:{item_name}] Invalid integrity hash (must be 64-char hex sha256)"
                )

    return errors, warnings


def check_permissions(plugin_name: str, data: Dict[str, Any]) -> List[str]:
    """
    Check that permissions are declared.

    Warnings for plugins missing permissions declaration.
    """
    warnings = []

    if "permissions" not in data:
        warnings.append("No 'permissions' field declared (recommended for security audit)")
        return warnings

    perms = data["permissions"]

    # Check for high-risk combinations
    if perms.get("exec") and perms.get("network"):
        warnings.append("Plugin has both 'exec' and 'network' permissions (review carefully)")

    if perms.get("trading") == "live":
        warnings.append("Plugin declares 'trading: live' (requires manual approval before use)")

    return warnings


def check_trading_config(plugin_name: str, data: Dict[str, Any]) -> List[str]:
    """
    Check that trading plugins have risk config path.
    """
    warnings = []

    perms = data.get("permissions", {})
    if perms.get("trading") in ("paper", "live"):
        config = data.get("configuration", {})
        if "riskConfigPath" not in config:
            warnings.append("Trading plugin missing 'configuration.riskConfigPath'")

    return warnings


def validate_plugin(plugin_path: Path, schema: Dict[str, Any]) -> Tuple[int, int]:
    """
    Validate one plugin.

    Returns:
        (error_count, warning_count)
    """
    plugin_name, data = load_plugin(plugin_path)

    print(f"\n{BLUE}Validating:{RESET} {plugin_name}")

    all_errors = []
    all_warnings = []

    # 1. Schema validation
    schema_errors = validate_schema(plugin_name, data, schema)
    all_errors.extend(schema_errors)

    # 2. Remote source checks
    source_errors, source_warnings = check_remote_sources(plugin_name, data)
    all_errors.extend(source_errors)
    all_warnings.extend(source_warnings)

    # 3. Permissions check
    perm_warnings = check_permissions(plugin_name, data)
    all_warnings.extend(perm_warnings)

    # 4. Trading config check
    trading_warnings = check_trading_config(plugin_name, data)
    all_warnings.extend(trading_warnings)

    # Print results
    if all_errors:
        for err in all_errors:
            print(f"  {RED}✗ ERROR:{RESET} {err}")

    if all_warnings:
        for warn in all_warnings:
            print(f"  {YELLOW}⚠ WARNING:{RESET} {warn}")

    if not all_errors and not all_warnings:
        print(f"  {GREEN}✓ PASS{RESET}")

    return len(all_errors), len(all_warnings)


def main():
    """Main entry point."""
    ROOT = Path(__file__).resolve().parents[1]
    SCHEMA_PATH = ROOT / "schemas" / "plugin.schema.json"
    PLUGINS_DIR = ROOT / "plugins"

    print("=" * 70)
    print("Claude Code Plugin Validator")
    print("=" * 70)

    # Load schema
    if not SCHEMA_PATH.exists():
        print(f"{RED}ERROR:{RESET} Schema not found at {SCHEMA_PATH}")
        sys.exit(1)

    schema = load_schema(SCHEMA_PATH)
    print(f"Loaded schema: {SCHEMA_PATH}")

    # Find all plugins
    plugin_files = sorted(PLUGINS_DIR.glob("*/plugin.json"))

    if not plugin_files:
        print(f"{YELLOW}WARNING:{RESET} No plugins found in {PLUGINS_DIR}")
        sys.exit(0)

    print(f"Found {len(plugin_files)} plugins\n")

    # Validate each
    total_errors = 0
    total_warnings = 0

    for plugin_path in plugin_files:
        errors, warnings = validate_plugin(plugin_path, schema)
        total_errors += errors
        total_warnings += warnings

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Plugins validated: {len(plugin_files)}")
    print(f"Total errors: {total_errors}")
    print(f"Total warnings: {total_warnings}")

    if total_errors == 0:
        print(f"\n{GREEN}✓ All validations PASSED{RESET}")
        sys.exit(0)
    else:
        print(f"\n{RED}✗ Validations FAILED{RESET}")
        print("Fix errors above before merging.")
        sys.exit(1)


if __name__ == "__main__":
    main()
