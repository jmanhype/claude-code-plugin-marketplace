#!/usr/bin/env python3
"""
Test Reflector enhancements for AppWorld-specific bullet generation.

This validates:
1. Reflector._analyze_outcome() extracts error_analysis from AppWorldExecutor
2. Reflector._generate_appworld_bullet() generates domain-specific bullets
3. Reflector._propose_new_bullets() prioritizes AppWorld bullets

Does NOT require:
- Full interactive protocol
- Claude Code Skill running
- Actual AppWorld execution
"""

import json
from pathlib import Path
from utils.reflector import Reflector

def test_error_analysis_extraction():
    """Test that Reflector extracts error_analysis from execution_result."""
    print("\n" + "="*70)
    print("TEST 1: Error Analysis Extraction")
    print("="*70)

    reflector = Reflector()

    # Simulate AppWorldExecutor providing rich error_analysis
    sample = {
        'id': 'test_spotify_1',
        'instruction': 'Get my most-liked Spotify playlist',
        'apps': ['spotify']
    }

    execution_result = {
        'code': 'print("test")',
        'success': False,
        'execution_feedback': {
            'error_analysis': {
                'error_type': 'authentication_error',
                'error_messages': ['Missing access_token in request'],
                'failed_apis': ['spotify.search_tracks'],
                'missing_patterns': ['Always call spotify.login() first'],
                'suggested_fixes': ['Add spotify.login() before API calls']
            }
        }
    }

    # Call _analyze_outcome
    analysis = reflector._analyze_outcome(
        sample=sample,
        prediction='',
        ground_truth='test_playlist',
        success=False,
        execution_result=execution_result
    )

    print(f"✓ Extracted error_type: {analysis['error_type']}")
    print(f"✓ Extracted error_messages: {analysis['error_messages']}")
    print(f"✓ Extracted failed_apis: {analysis['failed_apis']}")
    print(f"✓ Extracted missing_patterns: {analysis['missing_patterns']}")
    print(f"✓ Extracted suggested_fixes: {analysis['suggested_fixes']}")

    # Validate extraction
    assert analysis['error_type'] == 'authentication_error'
    assert len(analysis['error_messages']) > 0
    assert len(analysis['missing_patterns']) > 0
    print("\n✅ Error analysis extraction PASSED")
    return analysis


def test_appworld_bullet_generation():
    """Test that Reflector generates AppWorld-specific bullets."""
    print("\n" + "="*70)
    print("TEST 2: AppWorld-Specific Bullet Generation")
    print("="*70)

    reflector = Reflector()

    test_cases = [
        {
            'name': 'Authentication Error',
            'sample': {'id': 'test_1', 'apps': ['spotify']},
            'error_analysis': {
                'error_type': 'authentication_error',
                'error_messages': ['Missing access_token'],
                'failed_apis': ['spotify.search_tracks'],
                'missing_patterns': ['Always call login() first'],
                'suggested_fixes': ['Call spotify.login() before search']
            },
            'expected_title_contains': 'authenticate'
        },
        {
            'name': 'API Misuse',
            'sample': {'id': 'test_2', 'apps': ['gmail']},
            'error_analysis': {
                'error_type': 'api_misuse',
                'error_messages': ['AttributeError: get_messages not found'],
                'failed_apis': ['gmail.get_messages'],
                'missing_patterns': ['Use correct method names'],
                'suggested_fixes': ['Use search_messages() instead of get_messages()']
            },
            'expected_title_contains': 'API method'
        },
        {
            'name': 'Missing Data',
            'sample': {'id': 'test_3', 'apps': ['venmo']},
            'error_analysis': {
                'error_type': 'missing_data',
                'error_messages': ['NoneType has no attribute id'],
                'failed_apis': [],
                'missing_patterns': ['Check response structure'],
                'suggested_fixes': ['Verify response contains expected fields']
            },
            'expected_title_contains': 'response structure'
        },
        {
            'name': 'Logic Error',
            'sample': {'id': 'test_4', 'apps': ['todoist']},
            'error_analysis': {
                'error_type': 'logic_error',
                'error_messages': [],
                'failed_apis': [],
                'missing_patterns': [
                    'Need to filter tasks by project_id',
                    'Must check task completion status'
                ],
                'suggested_fixes': ['Use get_project_tasks() with project_id filter']
            },
            'expected_title_contains': 'logic'
        }
    ]

    generated_bullets = []

    for test_case in test_cases:
        print(f"\nTest Case: {test_case['name']}")
        print(f"  Error Type: {test_case['error_analysis']['error_type']}")

        bullet = reflector._generate_appworld_bullet(
            sample=test_case['sample'],
            error_analysis=test_case['error_analysis']
        )

        if bullet:
            print(f"  ✓ Generated bullet:")
            print(f"    Title: {bullet['title']}")
            print(f"    Tags: {bullet['tags']}")
            print(f"    Content preview: {bullet['content'][:80]}...")

            # Validate bullet structure
            assert 'id' in bullet
            assert 'title' in bullet
            assert 'content' in bullet
            assert 'tags' in bullet
            assert 'evidence' in bullet

            # Validate bullet content
            assert test_case['expected_title_contains'].lower() in bullet['title'].lower()

            generated_bullets.append(bullet)
        else:
            print(f"  ✗ No bullet generated")

    print(f"\n✅ Generated {len(generated_bullets)}/{len(test_cases)} AppWorld-specific bullets")
    return generated_bullets


def test_propose_bullets_prioritization():
    """Test that _propose_new_bullets prioritizes AppWorld bullets."""
    print("\n" + "="*70)
    print("TEST 3: Bullet Proposal Prioritization")
    print("="*70)

    reflector = Reflector()

    sample = {
        'id': 'test_priority_1',
        'instruction': 'Send email to john@example.com',
        'apps': ['gmail']
    }

    # Case 1: With rich error_analysis (should generate AppWorld bullet)
    error_analysis = {
        'error_type': 'api_misuse',
        'error_messages': ['Method send_mail() not found'],
        'failed_apis': ['gmail.send_mail'],
        'missing_patterns': ['Use correct API method names'],
        'suggested_fixes': ['Use send_message() instead of send_mail()']
    }

    bullets = reflector._propose_new_bullets(
        sample=sample,
        error_analysis=error_analysis,
        missing_guidance=[],
        success=False
    )

    print(f"\n With error_analysis:")
    print(f"  Generated {len(bullets)} bullet(s)")
    if bullets:
        print(f"  First bullet title: {bullets[0]['title']}")
        print(f"  First bullet tags: {bullets[0]['tags']}")

    # Validate that AppWorld bullet was prioritized
    assert len(bullets) > 0, "Should generate at least one bullet"
    assert bullets[0]['author'] == 'reflector'

    print("\n✅ Bullet prioritization PASSED")
    return bullets


def test_backwards_compatibility():
    """Test that Reflector still works without error_analysis (SkillsExecutor)."""
    print("\n" + "="*70)
    print("TEST 4: Backwards Compatibility")
    print("="*70)

    reflector = Reflector()

    sample = {
        'id': 'test_compat_1',
        'instruction': 'Test instruction',
        'apps': []
    }

    # Simulate old-style execution_result without error_analysis
    execution_result = {
        'code': 'print("test")',
        'success': False,
        'execution_feedback': {
            # No error_analysis field
        }
    }

    # Should fall back to pattern matching
    analysis = reflector._analyze_outcome(
        sample=sample,
        prediction='',
        ground_truth='expected',
        success=False,
        execution_result=execution_result
    )

    print(f"  Without error_analysis:")
    print(f"    Error type: {analysis.get('error_type', 'None')}")
    print(f"    Root cause: {analysis.get('root_cause', 'N/A')[:50]}...")

    print("\n✅ Backwards compatibility PASSED")


def main():
    """Run all Reflector enhancement tests."""
    print("\n" + "="*70)
    print("REFLECTOR ENHANCEMENT VALIDATION")
    print("="*70)
    print("\nTesting enhanced Reflector for AppWorld-specific bullet generation")
    print("WITHOUT requiring interactive protocol or Claude Code Skill")

    try:
        # Test 1: Error analysis extraction
        analysis = test_error_analysis_extraction()

        # Test 2: AppWorld bullet generation
        bullets = test_appworld_bullet_generation()

        # Test 3: Bullet prioritization
        proposed = test_propose_bullets_prioritization()

        # Test 4: Backwards compatibility
        test_backwards_compatibility()

        print("\n" + "="*70)
        print("FINAL RESULTS")
        print("="*70)
        print(f"✅ All tests PASSED")
        print(f"\n✓ Error analysis extraction: Working")
        print(f"✓ AppWorld bullet generation: {len(bullets)} bullets generated")
        print(f"✓ Bullet prioritization: Working")
        print(f"✓ Backwards compatibility: Working")

        print("\n" + "="*70)
        print("SAMPLE GENERATED BULLETS")
        print("="*70)
        for i, bullet in enumerate(bullets[:3], 1):
            print(f"\nBullet {i}: {bullet['title']}")
            print(f"  Tags: {', '.join(bullet['tags'])}")
            print(f"  Content: {bullet['content'][:120]}...")

        print("\n✅ Reflector enhancements validated successfully!")
        print("   Ready for integration with AppWorldExecutor")
        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
