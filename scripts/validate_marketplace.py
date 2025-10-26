#!/usr/bin/env python3
"""
Validate marketplace.json against Claude Code plugin requirements.

Guided by ACE bullet-2025-10-25-006:
"Validate JSON files before committing in plugin marketplace projects"
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def load_json(path: Path) -> Tuple[Dict, str]:
    """
    Load JSON file with robust error handling.

    Guided by bullet-2025-10-26-001:
    "Handle both flat and nested JSON structures in data processing scripts"
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data, ""
    except json.JSONDecodeError as e:
        return {}, f"Invalid JSON: {e}"
    except FileNotFoundError:
        return {}, f"File not found: {path}"


def validate_plugin_entry(plugin: Dict, index: int) -> List[str]:
    """Validate a single plugin entry."""
    errors = []
    # Actual marketplace.json uses minimal schema
    required = ["name", "source", "description"]

    for field in required:
        if field not in plugin:
            errors.append(f"Plugin {index}: Missing required field '{field}'")
        elif not plugin[field]:
            errors.append(f"Plugin {index}: Empty value for '{field}'")

    # Validate version format (semantic versioning)
    if "version" in plugin:
        version = plugin["version"]
        if not isinstance(version, str) or not version.count('.') >= 1:
            errors.append(f"Plugin {index}: Invalid version format '{version}' (expected: X.Y.Z)")

    # Validate repository URL
    if "repository" in plugin:
        repo = plugin["repository"]
        if repo and not repo.startswith(("https://", "http://")):
            errors.append(f"Plugin {index}: Invalid repository URL '{repo}'")

    return errors


def validate_marketplace(marketplace_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate marketplace.json file.

    Returns:
        (is_valid, error_list)
    """
    data, load_error = load_json(marketplace_path)
    if load_error:
        return False, [load_error]

    errors = []

    # Check top-level structure
    if "plugins" not in data:
        errors.append("Missing 'plugins' array at top level")
        return False, errors

    plugins = data["plugins"]
    if not isinstance(plugins, list):
        errors.append("'plugins' must be an array")
        return False, errors

    # Validate each plugin
    for i, plugin in enumerate(plugins, 1):
        if not isinstance(plugin, dict):
            errors.append(f"Plugin {i}: Must be an object, got {type(plugin).__name__}")
            continue

        errors.extend(validate_plugin_entry(plugin, i))

    # Check for duplicate plugin names
    names = [p.get("name") for p in plugins if isinstance(p, dict)]
    duplicates = [name for name in names if names.count(name) > 1]
    if duplicates:
        errors.append(f"Duplicate plugin names: {set(duplicates)}")

    return len(errors) == 0, errors


def main():
    """Main validation entry point."""
    if len(sys.argv) < 2:
        print("Usage: validate_marketplace.py <marketplace.json>")
        sys.exit(2)

    marketplace_path = Path(sys.argv[1])

    print(f"🔍 Validating {marketplace_path}...")
    is_valid, errors = validate_marketplace(marketplace_path)

    if is_valid:
        print("✅ Validation passed - marketplace.json is valid")
        sys.exit(0)
    else:
        print(f"❌ Validation failed - found {len(errors)} error(s):\\n")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
