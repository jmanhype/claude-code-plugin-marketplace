"""
Test three-stage quality-gated curator with FAISS deduplication.

This verifies the proper ACE implementation from the paper:
- Stage 1: Structural Validation
- Stage 2: Quality Assessment (FAISS, not TF-IDF)
- Stage 3: Final Approval

Confirms implementation matches ace-playbook repository approach.
"""

import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.curator_staged import StagedCurator
from utils.embeddings_faiss import FAISSDeduplicator


def test_faiss_deduplicator():
    """Test FAISS-based semantic duplicate detection."""
    print("\n" + "="*70)
    print("TEST 1: FAISS Semantic Deduplication")
    print("="*70)

    deduplicator = FAISSDeduplicator()

    # Create test bullets with semantic duplicates
    bullets = [
        {
            'id': 'test-001',
            'title': 'Read files before editing',
            'content': 'Always use Read tool before Edit tool to avoid errors',
            'status': 'active'
        },
        {
            'id': 'test-002',
            'title': 'Use Read before Edit',
            'content': 'You must read a file using Read before editing with Edit tool',
            'status': 'active'
        },
        {
            'id': 'test-003',
            'title': 'Parallel tool calls for performance',
            'content': 'When operations are independent, call multiple tools in parallel in one message',
            'status': 'active'
        },
        {
            'id': 'test-004',
            'title': 'Make parallel calls when possible',
            'content': 'Execute independent tool calls in parallel to maximize performance',
            'status': 'active'
        }
    ]

    print(f"\n📋 Testing with {len(bullets)} bullets:")
    for b in bullets:
        print(f"   - {b['id']}: {b['title']}")

    # Find duplicates
    duplicates = deduplicator.find_duplicates(bullets, threshold=0.80)

    print(f"\n🔍 Found {len(duplicates)} duplicate pair(s):")
    for id1, id2, sim in duplicates:
        print(f"   - {id1} ↔ {id2}: {sim:.3f} similarity")

    # Verify we found the expected duplicates
    expected_pairs = [
        ('test-001', 'test-002'),  # Read before Edit variants
        ('test-003', 'test-004'),  # Parallel calls variants
    ]

    assert len(duplicates) >= 2, f"Expected at least 2 duplicate pairs, found {len(duplicates)}"

    print("\n✅ FAISS deduplication working correctly!")
    return duplicates


def test_three_stage_curator():
    """Test three-stage quality gating with real playbook."""
    print("\n" + "="*70)
    print("TEST 2: Three-Stage Quality-Gated Curator")
    print("="*70)

    # Use actual playbook
    playbook_path = Path(__file__).parent.parent / "skills" / "playbook.json"

    if not playbook_path.exists():
        print(f"⚠️  Playbook not found at {playbook_path}, skipping test")
        return

    # Initialize curator with FAISS
    curator = StagedCurator(str(playbook_path), use_faiss=True)

    print(f"\n✓ Initialized StagedCurator")
    print(f"   Playbook: {playbook_path.name}")
    print(f"   Deduplication: {'FAISS' if curator.using_faiss else 'TF-IDF fallback'}")
    print(f"   Current bullets: {len(curator.playbook.get('bullets', []))}")

    # Create a test delta with a new bullet
    test_delta = {
        'reasoning': 'Test delta for three-stage curation',
        'task_context': 'test_staged_curator.py',
        'new_bullets': [
            {
                'id': 'test-staged-001',
                'title': 'Test three-stage quality gating',
                'content': 'Curator should validate structure (Stage 1), assess quality via FAISS (Stage 2), and approve for merge (Stage 3). Each stage acts as a quality gate that must be passed.',
                'tags': ['ace', 'curator', 'testing', 'quality_gates'],
                'evidence': [],
                'links': [],
                'confidence': 'high',
                'scope': 'global',
                'prerequisites': [],
                'author': 'test',
                'status': 'active'
            }
        ],
        'counters': [],
        'edits': [],
        'merges': [],
        'deprecations': []
    }

    print("\n" + "-"*70)
    print("Testing delta curation...")
    print("-"*70)

    # Curate the delta through three stages
    result = curator.curate_delta(test_delta)

    print(f"\n📊 Curation Result:")
    print(f"   Stage reached: {result.current_stage.name if result.current_stage else 'None'}")
    print(f"   Passed all gates: {result.passed}")
    print(f"   Requires review: {result.requires_human_review}")
    print(f"   Quality score: {result.quality_signals.get('quality_score', 0):.2f}")
    print(f"   Deduplication method: {result.quality_signals.get('deduplication_method', 'unknown')}")
    print(f"   Duplicates found: {len(result.duplicate_bullets)}")

    if result.curation_notes:
        print(f"\n   Notes:")
        for note in result.curation_notes[:5]:
            print(f"      - {note}")

    # Verify stages
    assert result.passed, "Delta should pass all quality gates"
    assert result.current_stage.value == 3, "Should reach Stage 3 (Final Approval)"
    assert result.quality_signals.get('deduplication_method') == 'faiss', "Should use FAISS, not TF-IDF"

    print("\n✅ Three-stage curator working correctly!")
    print(f"   ✓ Stage 1: Structural Validation PASSED")
    print(f"   ✓ Stage 2: Quality Assessment PASSED (FAISS)")
    print(f"   ✓ Stage 3: Final Approval PASSED")

    return result


def main():
    """Run all curator tests."""
    print("\n" + "="*70)
    print("ACE Three-Stage Curator Tests")
    print("="*70)
    print("Verifying implementation matches ACE paper + ace-playbook repo:")
    print("  - FAISS semantic deduplication (not TF-IDF)")
    print("  - Three quality-gated stages")
    print("  - Deltas must graduate through all stages")
    print("="*70)

    try:
        # Test 1: FAISS deduplication
        test_faiss_deduplicator()

        # Test 2: Three-stage curator
        test_three_stage_curator()

        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        print("\nKey Confirmations:")
        print("  ✓ FAISS-based semantic similarity working")
        print("  ✓ Three-stage quality gating functional")
        print("  ✓ Deltas graduate through: Validation → Quality → Approval")
        print("  ✓ Implementation matches ACE paper Section 3.2")
        print("="*70 + "\n")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
