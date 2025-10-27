"""
Three-Stage Quality-Gated Curator for ACE.

Implements the Curator workflow from ACE paper with explicit quality gates:
- Stage 1: Structural Validation
- Stage 2: Quality Assessment (FAISS deduplication, generalizability)
- Stage 3: Final Approval & Merge

Deltas must "graduate" through each stage to be merged into the playbook.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

try:
    from .embeddings_faiss import FAISSDeduplicator
    FAISS_AVAILABLE = True
except ImportError:
    print("⚠️  FAISS not available, falling back to TF-IDF (not recommended)")
    try:
        from .embeddings import EmbeddingsDeduplicator
    except ImportError:
        from embeddings import EmbeddingsDeduplicator
    FAISS_AVAILABLE = False


class CurationStage(Enum):
    """Quality gates that deltas must pass through."""
    STRUCTURAL_VALIDATION = 1
    QUALITY_ASSESSMENT = 2
    FINAL_APPROVAL = 3


class CurationResult:
    """Result of curation with stage information."""

    def __init__(self):
        self.current_stage = None
        self.passed = False
        self.clean_delta = None
        self.quality_signals = {}
        self.curation_notes = []
        self.requires_human_review = False
        self.duplicate_bullets = []
        self.normalized_tags = {}

    def to_dict(self) -> Dict:
        return {
            'current_stage': self.current_stage.value if self.current_stage else None,
            'passed': self.passed,
            'clean_delta': self.clean_delta,
            'quality_signals': self.quality_signals,
            'curation_notes': self.curation_notes,
            'requires_human_review': self.requires_human_review,
            'duplicate_bullets': self.duplicate_bullets,
            'normalized_tags': self.normalized_tags
        }


class StagedCurator:
    """
    Three-stage quality-gated Curator.

    Deltas must pass through quality gates in order:
    1. STRUCTURAL_VALIDATION: Syntax, required fields, delta format
    2. QUALITY_ASSESSMENT: FAISS deduplication, generalizability, counter validity
    3. FINAL_APPROVAL: All quality signals reviewed, merge decision

    Only deltas that graduate through all three stages are merged into the playbook.
    """

    def __init__(self, playbook_path: str, use_faiss: bool = True):
        """
        Args:
            playbook_path: Path to playbook JSON file
            use_faiss: Use FAISS for semantic deduplication (recommended)
        """
        self.playbook_path = Path(playbook_path)
        self.playbook = self._load_playbook()
        self.curation_history = []

        # Initialize deduplicator
        if use_faiss and FAISS_AVAILABLE:
            self.deduplicator = FAISSDeduplicator()
            self.using_faiss = True
        else:
            if use_faiss:
                print("⚠️  FAISS requested but not available, using TF-IDF fallback")
            self.deduplicator = EmbeddingsDeduplicator(use_embeddings=False)
            self.using_faiss = False

    def _load_playbook(self) -> Dict:
        """Load playbook from JSON file."""
        with open(self.playbook_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Handle both nested and flat structures
        if isinstance(data, dict) and 'bullets' in data:
            return data
        return {'bullets': data, 'metadata': {}}

    def _save_playbook(self):
        """Save playbook to JSON file."""
        with open(self.playbook_path, 'w', encoding='utf-8') as f:
            json.dump(self.playbook, f, indent=2)

    def curate_delta(self, delta: Dict[str, Any], sample: Optional[Dict] = None, execution_feedback: Optional[Dict] = None) -> CurationResult:
        """
        Curate delta through LLM synthesis + three quality-gated stages.

        This implements the ACE paper's two-phase Curator architecture:
        Phase 1: LLM synthesizes Reflector output into structured delta
        Phase 2: Three-stage quality gates (structural, quality, approval)

        Args:
            delta: Delta proposal from Reflector
            sample: Optional task sample metadata (for LLM-based synthesis)
            execution_feedback: Optional execution feedback (for LLM-based synthesis)

        Returns:
            CurationResult with stage, pass/fail, and clean delta if approved
        """
        result = CurationResult()

        print(f"\n{'='*60}")
        print(f"CURATOR: LLM Synthesis + Three-Stage Quality Gate Processing")
        print(f"{'='*60}")

        # PHASE 1: LLM-based delta synthesis (optional, if sample provided)
        if sample and execution_feedback:
            print(f"\n🎯 Phase 1: LLM-based Delta Synthesis")
            synthesized_delta = self._synthesize_delta_with_llm(delta, sample, execution_feedback)
            if synthesized_delta:
                delta = synthesized_delta
                result.curation_notes.append("LLM-based delta synthesis applied")
                print(f"   ✅ Using LLM-synthesized delta")
            else:
                result.curation_notes.append("Using original Reflector delta (LLM synthesis failed)")
                print(f"   ⚠️  LLM synthesis failed, using original delta")

        # PHASE 2: Three-stage quality gates
        print(f"\n📋 Stage 1: Structural Validation")
        result.current_stage = CurationStage.STRUCTURAL_VALIDATION

        stage1_passed, stage1_notes = self._stage1_structural_validation(delta)

        result.curation_notes.extend(stage1_notes)

        if not stage1_passed:
            result.passed = False
            result.requires_human_review = True
            print(f"   ❌ Stage 1 FAILED: {stage1_notes}")
            return result

        print(f"   ✅ Stage 1 PASSED: Delta structure valid")

        # STAGE 2: QUALITY ASSESSMENT
        print(f"\n🔍 Stage 2: Quality Assessment")
        result.current_stage = CurationStage.QUALITY_ASSESSMENT

        stage2_passed, stage2_signals, stage2_notes = self._stage2_quality_assessment(delta)

        result.quality_signals.update(stage2_signals)
        result.curation_notes.extend(stage2_notes)

        # Apply quality fixes (e.g., filter duplicates, normalize tags)
        delta_cleaned = self._apply_quality_fixes(delta, stage2_signals)

        if not stage2_passed:
            result.passed = False
            result.requires_human_review = True
            result.duplicate_bullets = stage2_signals.get('duplicates', [])
            print(f"   ❌ Stage 2 FAILED: Quality issues detected")
            for note in stage2_notes:
                print(f"      - {note}")
            return result

        print(f"   ✅ Stage 2 PASSED: Quality checks passed")
        for key, value in stage2_signals.items():
            if key != 'duplicates':
                print(f"      - {key}: {value}")

        # STAGE 3: FINAL APPROVAL
        print(f"\n✨ Stage 3: Final Approval")
        result.current_stage = CurationStage.FINAL_APPROVAL

        stage3_passed, stage3_notes = self._stage3_final_approval(
            delta_cleaned,
            stage2_signals
        )

        result.curation_notes.extend(stage3_notes)

        if not stage3_passed:
            result.passed = False
            result.requires_human_review = True
            print(f"   ❌ Stage 3 FAILED: Not approved for merge")
            return result

        # Wrap in clean delta format
        clean_delta = {
            'delta_id': f"delta-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'author': 'agent',
            'rationale': delta.get('reasoning', 'No rationale provided'),
            'task_context': delta.get('task_context', 'Unknown'),
            'reviewed': False,
            'curation_quality_signals': stage2_signals,
            **delta_cleaned
        }

        result.clean_delta = clean_delta
        result.passed = True
        result.duplicate_bullets = stage2_signals.get('duplicates', [])
        result.normalized_tags = stage2_signals.get('normalized_tags', {})

        print(f"   ✅ Stage 3 PASSED: Delta approved for merge")
        print(f"\n{'='*60}")
        print(f"CURATOR: Delta graduated through all quality gates")
        print(f"{'='*60}\n")

        # Store curation history
        self.curation_history.append({
            'delta_id': clean_delta['delta_id'],
            'timestamp': clean_delta['timestamp'],
            'stages_passed': [s.name for s in CurationStage],
            'quality_signals': stage2_signals,
            'notes': result.curation_notes
        })

        return result

    def _stage1_structural_validation(self, delta: Dict) -> Tuple[bool, List[str]]:
        """
        Stage 1: Validate delta structure and required fields.

        Checks:
        - Delta has at least one operation
        - New bullets have required fields (id, title, content)
        - Counter updates reference valid fields
        - No malformed JSON structures

        Returns:
            (passed, notes)
        """
        notes = []
        errors = []

        # Check for at least one operation
        operations = ['new_bullets', 'counters', 'edits', 'merges', 'deprecations']
        if not any(delta.get(op) for op in operations):
            errors.append("Delta has no operations")

        # Validate new_bullets structure
        for bullet in delta.get('new_bullets', []):
            if not bullet.get('id'):
                errors.append(f"Bullet missing id: {bullet}")
            if not bullet.get('title'):
                errors.append(f"Bullet {bullet.get('id')} missing title")
            if not bullet.get('content'):
                errors.append(f"Bullet {bullet.get('id')} missing content")
            if not isinstance(bullet.get('tags', []), list):
                errors.append(f"Bullet {bullet.get('id')} has invalid tags (not list)")

        # Validate counters structure (handles both dict and list formats)
        counters = delta.get('counters', {})
        if isinstance(counters, dict):
            # LLM returns dict format: {"bullet-id": {"helpful_count": 1, ...}}
            for bullet_id, counter_data in counters.items():
                if not isinstance(counter_data, dict):
                    errors.append(f"Counter for {bullet_id} is not a dict")
                # Check for either count fields (from LLM) or delta fields (legacy)
                if not any(k in counter_data for k in ['helpful_count', 'unhelpful_count', 'helpful_delta', 'harmful_delta']):
                    errors.append(f"Counter for {bullet_id} has no update values")
        elif isinstance(counters, list):
            # Legacy list format: [{"id": "bullet-id", "helpful_delta": 1, ...}]
            for counter in counters:
                if not counter.get('id'):
                    errors.append(f"Counter missing bullet id")
                if 'helpful_delta' not in counter and 'harmful_delta' not in counter:
                    errors.append(f"Counter {counter.get('id')} has no delta values")

        passed = len(errors) == 0

        if passed:
            notes.append(f"Validated {len(delta.get('new_bullets', []))} new bullet(s)")
            notes.append(f"Validated {len(delta.get('counters', []))} counter update(s)")
        else:
            notes.extend(errors)

        return passed, notes

    def _stage2_quality_assessment(
        self,
        delta: Dict
    ) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        Stage 2: Quality assessment using FAISS deduplication and heuristics.

        Checks:
        - FAISS-based semantic duplicate detection
        - Generalizability (not too task-specific)
        - Counter validity (references existing bullets)
        - Tag normalization

        Returns:
            (passed, quality_signals, notes)
        """
        signals = {}
        notes = []
        quality_issues = []

        # 1. FAISS Duplicate Detection
        if delta.get('new_bullets'):
            duplicates = self._check_duplicates_faiss(delta['new_bullets'])
            signals['duplicates'] = duplicates
            signals['deduplication_method'] = 'faiss' if self.using_faiss else 'tfidf_fallback'

            if duplicates:
                notes.append(
                    f"Found {len(duplicates)} potential duplicate(s) "
                    f"(using {signals['deduplication_method']})"
                )
                # Duplicates are a signal, not necessarily a failure
                # Will be filtered in apply_quality_fixes

        # 2. Generalizability Check
        if delta.get('new_bullets'):
            task_specific = self._check_generalizability(delta['new_bullets'])
            signals['task_specific_bullets'] = task_specific

            if task_specific:
                notes.append(f"Warning: {len(task_specific)} bullet(s) may be task-specific")
                # This is a warning, not a hard failure (could require human review)

        # 3. Counter Validity
        if delta.get('counters'):
            invalid_counters = self._validate_counters(delta['counters'])
            signals['invalid_counters'] = invalid_counters

            if invalid_counters:
                quality_issues.append(f"Found {len(invalid_counters)} invalid counter(s)")

        # 4. Tag Normalization
        if delta.get('new_bullets'):
            normalized_tags = {}
            for bullet in delta['new_bullets']:
                original_tags = bullet.get('tags', [])
                normalized = self._normalize_tags(original_tags)
                normalized_tags[bullet['id']] = {
                    'original': original_tags,
                    'normalized': normalized
                }
            signals['normalized_tags'] = normalized_tags
            notes.append(f"Normalized tags for {len(normalized_tags)} bullet(s)")

        # Overall quality assessment
        signals['quality_score'] = self._compute_quality_score(signals)

        # Pass if no hard failures (invalid counters are hard failures)
        passed = len(quality_issues) == 0

        if not passed:
            notes.extend(quality_issues)

        return passed, signals, notes

    def _stage3_final_approval(
        self,
        delta: Dict,
        quality_signals: Dict
    ) -> Tuple[bool, List[str]]:
        """
        Stage 3: Final approval based on quality signals.

        Reviews all quality signals and makes final merge decision.

        Decision criteria:
        - Quality score above threshold
        - No critical issues
        - Adds value to playbook

        Returns:
            (approved, notes)
        """
        notes = []

        quality_score = quality_signals.get('quality_score', 0.0)
        duplicates_removed = len(quality_signals.get('duplicates', []))
        task_specific_count = len(quality_signals.get('task_specific_bullets', []))

        notes.append(f"Quality score: {quality_score:.2f}")
        notes.append(f"Duplicates removed: {duplicates_removed}")
        notes.append(f"Task-specific bullets: {task_specific_count}")

        # Approval threshold
        QUALITY_THRESHOLD = 0.6

        if quality_score < QUALITY_THRESHOLD:
            notes.append(f"Quality score below threshold ({QUALITY_THRESHOLD})")
            return False, notes

        # Check if delta adds meaningful content
        remaining_bullets = len(delta.get('new_bullets', []))

        # Handle both dict and list counter formats
        counters = delta.get('counters', {})
        if isinstance(counters, dict):
            remaining_counters = len(counters)
        else:
            remaining_counters = len(counters)

        if remaining_bullets == 0 and remaining_counters == 0:
            notes.append("No meaningful content after quality filtering")
            return False, notes

        notes.append(f"Approved: {remaining_bullets} bullet(s), {remaining_counters} counter(s)")
        return True, notes

    def _check_duplicates_faiss(
        self,
        new_bullets: List[Dict]
    ) -> List[Tuple[str, str, float]]:
        """
        Check for duplicates using FAISS semantic similarity.

        Returns:
            List of (new_bullet_id, existing_bullet_id, similarity) tuples
        """
        existing_bullets = self.playbook.get('bullets', [])
        all_bullets = existing_bullets + new_bullets

        # Find duplicates
        all_duplicates = self.deduplicator.find_duplicates(all_bullets, threshold=0.85)

        # Filter to only include pairs with one new and one existing
        new_bullet_ids = set(b['id'] for b in new_bullets)
        duplicates = []

        for id1, id2, sim in all_duplicates:
            if id1 in new_bullet_ids and id2 not in new_bullet_ids:
                duplicates.append((id1, id2, sim))
            elif id2 in new_bullet_ids and id1 not in new_bullet_ids:
                duplicates.append((id2, id1, sim))

        return duplicates

    def _check_generalizability(self, new_bullets: List[Dict]) -> List[str]:
        """
        Check if bullets are too task-specific.

        Heuristic: Look for specific IDs, dates, names.

        Returns:
            List of potentially task-specific bullet IDs
        """
        task_specific = []

        for bullet in new_bullets:
            content = bullet.get('content', '').lower()
            title = bullet.get('title', '').lower()

            # Specificity indicators
            specificity_patterns = [
                r'task-\d+',
                r'user-\d+',
                r'2025-\d{2}-\d{2}',
                r'channel-\d+',
                r'alice|bob|charlie',  # Example user names
            ]

            for pattern in specificity_patterns:
                if re.search(pattern, content) or re.search(pattern, title):
                    task_specific.append(bullet['id'])
                    break

        return task_specific

    def _validate_counters(self, counters) -> List[str]:
        """
        Validate counter updates reference existing bullets.
        Handles both dict and list formats.

        Returns:
            List of invalid bullet IDs
        """
        existing_ids = set(b['id'] for b in self.playbook.get('bullets', []))
        invalid = []

        if isinstance(counters, dict):
            # LLM format: {"bullet-id": {...}}
            for bullet_id in counters.keys():
                if bullet_id not in existing_ids:
                    invalid.append(bullet_id)
        elif isinstance(counters, list):
            # Legacy format: [{"id": "bullet-id", ...}]
            for counter in counters:
                bullet_id = counter.get('id')
                if bullet_id not in existing_ids:
                    invalid.append(bullet_id)

        return invalid

    def _normalize_tags(self, tags: List[str]) -> List[str]:
        """
        Normalize tags to follow taxonomy.

        Rules:
        - Hierarchical dot notation (tool.edit, not edit)
        - Lowercase
        - Consistent naming
        """
        normalized = []
        tag_map = {
            'edit': 'tool.edit',
            'read': 'tool.read',
            'write': 'tool.write',
            'bash': 'tool.bash',
            'git': 'git',
            'commit': 'git.commit',
            'push': 'git.push',
            'api': 'api',
            'apis': 'api',
            'validation': 'validation',
            'validate': 'validation',
        }

        for tag in tags:
            tag_lower = tag.lower().strip()
            normalized_tag = tag_map.get(tag_lower, tag_lower)
            if normalized_tag not in normalized:
                normalized.append(normalized_tag)

        return normalized

    def _compute_quality_score(self, signals: Dict) -> float:
        """
        Compute overall quality score from signals.

        Score components:
        - Base score: 0.5
        - No duplicates: +0.3
        - No task-specific bullets: +0.2
        - Using FAISS: +0.1 bonus

        Returns:
            Quality score in [0, 1]
        """
        score = 0.5  # Base

        # Deduplication quality
        if len(signals.get('duplicates', [])) == 0:
            score += 0.3
        elif len(signals.get('duplicates', [])) <= 2:
            score += 0.15

        # Generalizability
        if len(signals.get('task_specific_bullets', [])) == 0:
            score += 0.2

        # FAISS bonus
        if signals.get('deduplication_method') == 'faiss':
            score += 0.1

        return min(score, 1.0)

    def _apply_quality_fixes(self, delta: Dict, signals: Dict) -> Dict:
        """
        Apply quality fixes based on stage 2 signals.

        Fixes:
        - Remove duplicate bullets
        - Apply normalized tags
        - Filter invalid counters
        """
        delta_cleaned = delta.copy()

        # Remove duplicates
        if delta_cleaned.get('new_bullets'):
            duplicate_ids = set(d[0] for d in signals.get('duplicates', []))
            delta_cleaned['new_bullets'] = [
                b for b in delta_cleaned['new_bullets']
                if b['id'] not in duplicate_ids
            ]

        # Apply normalized tags
        if delta_cleaned.get('new_bullets'):
            normalized_tags = signals.get('normalized_tags', {})
            for bullet in delta_cleaned['new_bullets']:
                if bullet['id'] in normalized_tags:
                    bullet['tags'] = normalized_tags[bullet['id']]['normalized']

        # Filter invalid counters (handle both dict and list formats)
        if delta_cleaned.get('counters'):
            invalid_counter_ids = set(signals.get('invalid_counters', []))
            counters = delta_cleaned['counters']

            if isinstance(counters, dict):
                # LLM format: remove invalid keys
                delta_cleaned['counters'] = {
                    k: v for k, v in counters.items()
                    if k not in invalid_counter_ids
                }
            elif isinstance(counters, list):
                # Legacy format: remove invalid items
                delta_cleaned['counters'] = [
                    c for c in counters
                    if c.get('id') not in invalid_counter_ids
                ]

        return delta_cleaned

    def merge_delta(self, delta: Dict[str, Any]) -> bool:
        """
        Merge approved delta into playbook.

        Applies operations deterministically (non-LLM logic):
        1. Update counters
        2. Add new bullets
        3. Apply edits
        4. Execute merges
        5. Process deprecations
        6. Update metadata

        Returns:
            True if merge succeeded
        """
        try:
            print(f"\n📝 Merging delta into playbook...")

            # 1. Update counters (handle both dict and list formats)
            counters = delta.get('counters', {})
            if isinstance(counters, dict):
                # LLM format: {"bullet-id": {"helpful_count": 1, ...}}
                for bullet_id, counter_data in counters.items():
                    # Convert dict format to legacy format for _apply_counter_update
                    counter_dict = {'id': bullet_id}
                    # Handle both absolute counts and deltas
                    if 'helpful_count' in counter_data:
                        counter_dict['helpful_delta'] = counter_data['helpful_count']
                    if 'unhelpful_count' in counter_data:
                        counter_dict['harmful_delta'] = counter_data['unhelpful_count']
                    if 'helpful_delta' in counter_data:
                        counter_dict['helpful_delta'] = counter_data['helpful_delta']
                    if 'harmful_delta' in counter_data:
                        counter_dict['harmful_delta'] = counter_data['harmful_delta']
                    self._apply_counter_update(counter_dict)
            elif isinstance(counters, list):
                # Legacy format: [{"id": "bullet-id", "helpful_delta": 1, ...}]
                for counter in counters:
                    self._apply_counter_update(counter)

            # 2. Add new bullets
            for new_bullet in delta.get('new_bullets', []):
                self._add_bullet(new_bullet)

            # 3. Apply edits
            for edit in delta.get('edits', []):
                self._apply_edit(edit)

            # 4. Execute merges
            for merge in delta.get('merges', []):
                self._apply_merge(merge)

            # 5. Process deprecations
            for deprecation in delta.get('deprecations', []):
                self._apply_deprecation(deprecation)

            # 6. Update metadata
            self._update_metadata()

            # Save playbook
            self._save_playbook()

            print(f"   ✅ Delta merged successfully")
            return True

        except Exception as e:
            print(f"   ❌ Error merging delta: {e}")
            return False

    def _apply_counter_update(self, counter: Dict):
        """Apply counter update to bullet."""
        bullet_id = counter['id']
        for bullet in self.playbook.get('bullets', []):
            if bullet['id'] == bullet_id:
                bullet['helpful_count'] = bullet.get('helpful_count', 0) + counter.get('helpful_delta', 0)
                bullet['harmful_count'] = bullet.get('harmful_count', 0) + counter.get('harmful_delta', 0)
                bullet['last_updated'] = datetime.now().isoformat()
                break

    def _add_bullet(self, new_bullet: Dict):
        """Add new bullet to playbook."""
        new_bullet.setdefault('created', datetime.now().isoformat())
        new_bullet.setdefault('last_updated', datetime.now().isoformat())
        new_bullet.setdefault('helpful_count', 0)
        new_bullet.setdefault('harmful_count', 0)
        new_bullet.setdefault('status', 'active')

        self.playbook.setdefault('bullets', []).append(new_bullet)

    def _apply_edit(self, edit: Dict):
        """Apply edit to existing bullet."""
        bullet_id = edit['id']
        for bullet in self.playbook.get('bullets', []):
            if bullet['id'] == bullet_id:
                bullet.update(edit.get('set', {}))
                bullet['last_updated'] = datetime.now().isoformat()
                break

    def _apply_merge(self, merge: Dict):
        """Apply merge operation."""
        keep_id = merge['keep_id']
        merge_ids = merge['merge_ids']

        keep_bullet = None
        for bullet in self.playbook.get('bullets', []):
            if bullet['id'] == keep_id:
                keep_bullet = bullet
                break

        if not keep_bullet:
            return

        # Merge counters and archive merged bullets
        for merge_id in merge_ids:
            for bullet in self.playbook.get('bullets', []):
                if bullet['id'] == merge_id:
                    keep_bullet['helpful_count'] += bullet.get('helpful_count', 0)
                    keep_bullet['harmful_count'] += bullet.get('harmful_count', 0)
                    bullet['status'] = 'archived'
                    bullet['deprecation_reason'] = f"Merged into {keep_id}"
                    bullet['last_updated'] = datetime.now().isoformat()
                    break

        if 'merged_content' in merge:
            keep_bullet['content'] = merge['merged_content']

        keep_bullet['last_updated'] = datetime.now().isoformat()

    def _apply_deprecation(self, deprecation: Dict):
        """Apply deprecation."""
        bullet_id = deprecation['id']
        for bullet in self.playbook.get('bullets', []):
            if bullet['id'] == bullet_id:
                bullet['status'] = 'deprecated'
                bullet['deprecation_reason'] = deprecation['reason']
                bullet['last_updated'] = datetime.now().isoformat()
                break

    def _update_metadata(self):
        """Update playbook metadata."""
        bullets = self.playbook.get('bullets', [])
        metadata = self.playbook.setdefault('metadata', {})

        metadata['total_bullets'] = len(bullets)
        metadata['active_bullets'] = sum(1 for b in bullets if b.get('status') == 'active')
        metadata['deprecated_bullets'] = sum(1 for b in bullets if b.get('status') == 'deprecated')
        metadata['archived_bullets'] = sum(1 for b in bullets if b.get('status') == 'archived')
        metadata['last_curated'] = datetime.now().isoformat()

    def get_curation_history(self) -> List[Dict]:
        """Return curation history."""
        return self.curation_history.copy()

    def _synthesize_delta_with_llm(self, delta: Dict[str, Any], sample: Dict, execution_feedback: Dict) -> Optional[Dict]:
        """
        Use LLM (via curate-delta skill) to synthesize Reflector output into structured delta.

        This implements Phase 1 of the ACE paper's Curator architecture:
        "The Curator then synthesizes these lessons into compact delta entries..."

        Args:
            delta: Delta from Reflector
            sample: Task sample metadata
            execution_feedback: Execution feedback

        Returns:
            Synthesized delta dict or None if invocation fails
        """
        print(f"\n🔍 DEBUG StagedCurator._synthesize_delta_with_llm:")

        try:
            # Import skill invoker from same utils directory
            from . import claude_code_skill_invoker as skill_invoker
            import json

            # Build OPTIMIZED prompt for curate-delta skill (reduce from 11k+ chars)
            task_instruction = sample.get('instruction', 'Unknown')[:200]  # Truncate long instructions
            task_outcome = 'Success' if execution_feedback.get('tgc', 0) == 1.0 else 'Failure'

            # SUMMARIZE execution feedback instead of full dump
            error_analysis = execution_feedback.get('error_analysis', {})

            # Extract ONLY essential information
            feedback_summary = {
                'tgc': execution_feedback.get('tgc', 0),
                'sgc': execution_feedback.get('sgc', 0),
                'turns_used': execution_feedback.get('turns_used', 0),
                'error_type': error_analysis.get('error_type', 'unknown'),
                'error_messages': error_analysis.get('error_messages', [])[:3],  # Max 3 errors
                'missing_patterns': error_analysis.get('missing_patterns', [])[:3],  # Max 3 patterns
                'failed_apis': error_analysis.get('failed_apis', [])[:5]  # Max 5 APIs
            }

            # Also simplify delta - remove verbose fields
            simplified_delta = {
                'new_bullets': delta.get('new_bullets', [])[:5],  # Max 5 bullets
                'counters': delta.get('counters', {}),
                'error_type': delta.get('error_type', 'unknown')
            }

            skill_prompt = f"""# Task Metadata
Instruction: {task_instruction}
Outcome: {task_outcome} (TGC: {feedback_summary['tgc']}, SGC: {feedback_summary['sgc']})

## Execution Summary
- Turns used: {feedback_summary['turns_used']}
- Error type: {feedback_summary['error_type']}
- Error messages: {', '.join(feedback_summary['error_messages'])}
- Missing patterns: {', '.join(feedback_summary['missing_patterns'])}
- Failed APIs: {', '.join(feedback_summary['failed_apis'])}

## Reflector's Proposed Delta
```json
{json.dumps(simplified_delta, indent=2)}
```

## Your Task
Synthesize the Reflector's output into a high-quality delta proposal.
- Validate bullet quality (specific, actionable, evidence-backed)
- Check for redundancy with existing bullets
- Structure counter updates for bullet feedback
- Provide curation notes and quality assessment
"""

            print(f"   🎯 Invoking curate-delta skill (optimized prompt: {len(skill_prompt)} chars)...")
            response = skill_invoker.invoke_skill("curate-delta", skill_prompt)
            print(f"   ✅ LLM-powered curation successful ({len(response)} chars)")

            # Debug: Show the raw response
            print(f"   🔍 Raw LLM response preview (first 300 chars): {response[:300]}")

            # Parse JSON response (handle markdown code fences)
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
                if response_clean.endswith('```'):
                    response_clean = response_clean[:-3]
                response_clean = response_clean.strip()
            elif response_clean.startswith('```'):
                # Handle plain ``` without json specifier
                response_clean = response_clean[3:]
                if response_clean.endswith('```'):
                    response_clean = response_clean[:-3]
                response_clean = response_clean.strip()

            # Debug: Show cleaned response
            print(f"   🔍 Cleaned response preview (first 300 chars): {response_clean[:300]}")

            # Try to parse as JSON - if it fails, try to extract the delta directly
            try:
                result = json.loads(response_clean)
                synthesized_delta = result.get('delta')
            except json.JSONDecodeError as e:
                print(f"   ⚠️  JSON parse error: {e}")
                print(f"   🔧 Attempting to use original delta format...")
                # If LLM returns the delta directly without wrapping
                try:
                    synthesized_delta = json.loads(response_clean)
                except:
                    # If all else fails, try to find JSON in the response
                    import re
                    json_match = re.search(r'\{.*\}', response_clean, re.DOTALL)
                    if json_match:
                        try:
                            synthesized_delta = json.loads(json_match.group())
                            print(f"   ✅ Extracted JSON from response")
                        except:
                            synthesized_delta = None
                    else:
                        synthesized_delta = None

            if synthesized_delta:
                print(f"   ✅ RETURNING LLM-SYNTHESIZED DELTA")
                print(f"      New bullets: {len(synthesized_delta.get('new_bullets', []))}")
                print(f"      Counter updates: {len(synthesized_delta.get('counters', {}))}")
                return synthesized_delta
            else:
                print(f"   ❌ LLM response missing 'delta' key")
                return None

        except Exception as e:
            print(f"   ⚠️  Skill invocation failed: {e}")
            return None
