#!/usr/bin/env python3
# .claude/skills/ace-context-engineering/scripts/validate_delta.py
# Purpose: Validate ACE delta/bullets and generator/reflector/curator outputs against schemas

import json
import sys
import pathlib
from jsonschema import Draft7Validator, RefResolver

# Schema directory
BASE = pathlib.Path(__file__).resolve().parents[1] / "schemas"

def load(p):
    """Load JSON file"""
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))

def validate(data, schema_file):
    """Validate data against schema with reference resolution"""
    schema = load(BASE / schema_file)
    resolver = RefResolver(base_uri=f"file://{BASE}/", referrer=schema)
    Draft7Validator(schema, resolver=resolver).validate(data)

def main():
    if len(sys.argv) < 3:
        print("Usage: validate_delta.py <type> <json_path>")
        print("Types: delta bullet gen reflect curator feedback")
        sys.exit(2)

    typ, path = sys.argv[1], sys.argv[2]
    data = load(path)

    # Map type to schema file
    schema_map = {
        "delta": "delta.schema.json",
        "bullet": "bullet.schema.json",
        "gen": "generator_output.schema.json",
        "reflect": "reflector_output.schema.json",
        "curator": "curator_output.schema.json",
        "feedback": "feedback_event.schema.json"
    }

    if typ not in schema_map:
        print(f"Error: Unknown type '{typ}'")
        print(f"Valid types: {', '.join(schema_map.keys())}")
        sys.exit(1)

    try:
        validate(data, schema_map[typ])
        print(f"✅ Valid {typ}: {path}")
    except Exception as e:
        print(f"❌ Invalid {typ}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
