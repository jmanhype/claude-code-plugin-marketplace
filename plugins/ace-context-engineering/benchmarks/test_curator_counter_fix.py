#!/usr/bin/env python3
"""
Test the Curator's counter validation with both dict and list formats.
"""

import sys
import json
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / 'utils'))

# Import with package context
sys.path.insert(0, str(Path(__file__).parent))
from utils.curator_staged import StagedCurator

def test_counter_formats():
    """Test that Curator handles both dict and list counter formats."""

    # Create a curator instance
    curator = StagedCurator(
        playbook_path='/Users/speed/claude-code-plugin-marketplace/plugins/ace-context-engineering/skills/playbook.json',
        use_faiss=False  # Skip FAISS for simple test
    )

    print("=" * 80)
    print("Testing Curator Counter Format Handling")
    print("=" * 80)

    # Test 1: LLM dict format (what the curate-delta skill returns)
    print("\n🧪 Test 1: LLM dict-of-dicts format")
    delta_dict_format = {
        'new_bullets': [],
        'counters': {
            'bullet-2025-10-27-025940': {
                'unhelpful_count': 1
            },
            'appworld-spotify-005': {
                'unhelpful_count': 1
            },
            'appworld-complete-003': {
                'helpful_count': 1
            }
        }
    }

    try:
        passed, notes = curator._stage1_structural_validation(delta_dict_format)
        if passed:
            print("   ✅ PASSED: Dict format validated successfully")
            for note in notes:
                print(f"      {note}")
        else:
            print("   ❌ FAILED: Dict format validation failed")
            for note in notes:
                print(f"      ERROR: {note}")
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Legacy list format (what Reflector might pass)
    print("\n🧪 Test 2: Legacy list format")
    delta_list_format = {
        'new_bullets': [],
        'counters': [
            {'id': 'bullet-2025-10-27-025940', 'harmful_delta': 1},
            {'id': 'appworld-spotify-005', 'harmful_delta': 1},
            {'id': 'appworld-complete-003', 'helpful_delta': 1}
        ]
    }

    try:
        passed, notes = curator._stage1_structural_validation(delta_list_format)
        if passed:
            print("   ✅ PASSED: List format validated successfully")
            for note in notes:
                print(f"      {note}")
        else:
            print("   ❌ FAILED: List format validation failed")
            for note in notes:
                print(f"      ERROR: {note}")
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: Full curation with LLM dict format
    print("\n🧪 Test 3: Full curation with dict format")
    sample = {'instruction': 'Test task'}
    execution_feedback = {
        'tgc': 0.5,
        'sgc': 0.5,
        'error_analysis': {
            'error_type': 'logic_error',
            'error_messages': ['Test failed'],
            'missing_patterns': [],
            'failed_apis': []
        }
    }

    try:
        # Don't use LLM synthesis for this test
        result = curator.curate_delta(delta_dict_format)
        if result.passed:
            print("   ✅ PASSED: Full curation succeeded")
            print(f"      Stage reached: {result.current_stage}")
            print(f"      Notes: {result.curation_notes}")
        else:
            print("   ❌ FAILED: Full curation failed")
            print(f"      Stage: {result.current_stage}")
            print(f"      Notes: {result.curation_notes}")
    except Exception as e:
        print(f"   ❌ EXCEPTION during full curation: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("Test complete!")
    print("=" * 80)

if __name__ == "__main__":
    test_counter_formats()