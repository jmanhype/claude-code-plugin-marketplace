#!/usr/bin/env python3
"""Test what happens when result is empty string"""
import json

# Simulate the response structure we're seeing
response_json = {
    'type': 'result',
    'subtype': 'success',
    'is_error': False,
    'duration_ms': 1000,
    'duration_api_ms': 900,
    'num_turns': 1,
    'result': '',  # Empty string
    'session_id': 'test',
    'total_cost_usd': 0.01,
    'usage': {},
    'modelUsage': {},
    'permission_denials': [],
    'uuid': 'test-uuid'
}

print("Testing empty result field handling...")
print(f"Keys: {list(response_json.keys())}")

result_text = response_json.get('result', '')
print(f"Result value: '{result_text}'")
print(f"Result is empty string: {result_text == ''}")
print(f"Result is falsy: {not result_text}")

# This is what's happening in the code
if not result_text:
    print("⚠️ Result is empty, would fall back to other fields")