"""
Curator: Validates and merges deltas into playbook.

Based on ACE paper Section 3.1 and Appendix D Figure 11.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from .embeddings import EmbeddingsDeduplicator


class Curator:
    """
    Curates delta proposals from Reflector:
    - Validates delta structure and content
    - Checks for duplicates using embeddings
    - Normalizes tags and formatting
    - Merges approved deltas into playbook
    """

    def __init__(self, playbook_path: str, use_embeddings: bool = False):
        self.playbook_path = Path(playbook_path)
        self.playbook = self._load_playbook()
        self.deduplicator = EmbeddingsDeduplicator(use_embeddings=use_embeddings)
        self.curation_history = []

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

    def curate_delta(self, delta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize delta proposal.

        Args:
            delta: Delta from Reflector with new_bullets, counters, etc.

        Returns:
            {
                'clean_delta': {...},
                'curation_notes': '...',
                'requires_human_review': bool,
                'duplicate_bullets': [...],
                'normalized_tags': {...}
            }
        """
        curation_result = {
            'clean_delta': None,
            'curation_notes': [],
            'requires_human_review': False,
            'duplicate_bullets': [],
            'normalized_tags': {}
        }

        # 1. Validate delta structure
        validation_result = self._validate_delta_structure(delta)
        if not validation_result['valid']:
            curation_result['curation_notes'].append(
                f"Invalid delta structure: {validation_result['errors']}"
            )
            curation_result['requires_human_review'] = True
            return curation_result

        # 2. Check for duplicate bullets
        if delta.get('new_bullets'):
            duplicates = self._check_duplicates(delta['new_bullets'])
            if duplicates:
                curation_result['duplicate_bullets'] = duplicates
                curation_result['curation_notes'].append(
                    f"Found {len(duplicates)} potential duplicate(s), removed from delta"
                )
                # Filter out duplicates
                delta['new_bullets'] = [
                    b for b in delta['new_bullets']
                    if b['id'] not in [d[0] for d in duplicates]
                ]

        # 3. Normalize tags
        if delta.get('new_bullets'):
            for bullet in delta['new_bullets']:
                normalized = self._normalize_tags(bullet.get('tags', []))
                bullet['tags'] = normalized
                curation_result['normalized_tags'][bullet['id']] = normalized

        # 4. Validate counter updates
        if delta.get('counters'):
            invalid_counters = self._validate_counters(delta['counters'])
            if invalid_counters:
                curation_result['curation_notes'].append(
                    f"Removed {len(invalid_counters)} invalid counter(s)"
                )
                delta['counters'] = [
                    c for c in delta['counters']
                    if c['id'] not in invalid_counters
                ]

        # 5. Check generalizability
        if delta.get('new_bullets'):
            task_specific = self._check_generalizability(delta['new_bullets'])
            if task_specific:
                curation_result['curation_notes'].append(
                    f"Warning: {len(task_specific)} bullet(s) may be task-specific"
                )
                curation_result['requires_human_review'] = True

        # 6. Wrap in clean delta format
        clean_delta = {
            'delta_id': f"delta-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'author': 'agent',
            'rationale': delta.get('reasoning', 'No rationale provided'),
            'task_context': delta.get('task_context', 'Unknown'),
            'reviewed': False,
            **delta
        }

        curation_result['clean_delta'] = clean_delta

        # Store curation
        self.curation_history.append({
            'delta_id': clean_delta['delta_id'],
            'timestamp': clean_delta['timestamp'],
            'notes': curation_result['curation_notes'],
            'requires_review': curation_result['requires_human_review']
        })

        return curation_result

    def merge_delta(self, delta: Dict[str, Any]) -> bool:
        """
        Merge delta into playbook.

        Applies operations in order:
        1. Update counters
        2. Add new bullets
        3. Apply edits
        4. Execute merges
        5. Process deprecations
        6. Update metadata

        Returns:
            True if merge succeeded, False otherwise
        """
        try:
            # 1. Update counters
            for counter in delta.get('counters', []):
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

            return True

        except Exception as e:
            print(f"Error merging delta: {e}")
            return False

    def _validate_delta_structure(self, delta: Dict) -> Dict[str, Any]:
        """Validate delta has required structure."""
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

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    def _check_duplicates(self, new_bullets: List[Dict]) -> List[Tuple[str, str, float]]:
        """
        Check if new bullets are duplicates of existing ones.

        Returns:
            List of (new_bullet_id, existing_bullet_id, similarity) tuples
        """
        existing_bullets = self.playbook.get('bullets', [])
        all_bullets = existing_bullets + new_bullets

        # Find all duplicates
        all_duplicates = self.deduplicator.find_duplicates(all_bullets, threshold=0.80)

        # Filter to only include pairs with one new and one existing bullet
        new_bullet_ids = set(b['id'] for b in new_bullets)
        duplicates = []

        for id1, id2, sim in all_duplicates:
            if id1 in new_bullet_ids and id2 not in new_bullet_ids:
                duplicates.append((id1, id2, sim))
            elif id2 in new_bullet_ids and id1 not in new_bullet_ids:
                duplicates.append((id2, id1, sim))

        return duplicates

    def _normalize_tags(self, tags: List[str]) -> List[str]:
        """
        Normalize tags to follow taxonomy.

        Rules:
        - Use hierarchical dot notation (tool.edit, not edit)
        - Lowercase
        - Consistent naming (use 'api' not 'apis')
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

    def _validate_counters(self, counters: List[Dict]) -> List[str]:
        """
        Validate counter updates reference existing bullets.

        Returns:
            List of invalid bullet IDs
        """
        existing_ids = set(b['id'] for b in self.playbook.get('bullets', []))
        invalid = []

        for counter in counters:
            bullet_id = counter.get('id')
            if bullet_id not in existing_ids:
                invalid.append(bullet_id)

        return invalid

    def _check_generalizability(self, new_bullets: List[Dict]) -> List[str]:
        """
        Check if bullets are too task-specific.

        Heuristic: Bullets mentioning specific names, IDs, or dates may be task-specific.

        Returns:
            List of potentially task-specific bullet IDs
        """
        task_specific = []

        for bullet in new_bullets:
            content = bullet.get('content', '').lower()
            title = bullet.get('title', '').lower()

            # Check for specificity indicators
            specificity_indicators = [
                r'task-\d+',  # Task IDs
                r'user-\d+',  # User IDs
                r'2025-\d{2}-\d{2}',  # Specific dates
                r'channel-\d+',  # Channel IDs
                r'alice|bob|charlie',  # Specific names (example users)
            ]

            import re
            for pattern in specificity_indicators:
                if re.search(pattern, content) or re.search(pattern, title):
                    task_specific.append(bullet['id'])
                    break

        return task_specific

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
        # Ensure required fields
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
                    # Combine counters
                    keep_bullet['helpful_count'] += bullet.get('helpful_count', 0)
                    keep_bullet['harmful_count'] += bullet.get('harmful_count', 0)
                    # Archive
                    bullet['status'] = 'archived'
                    bullet['deprecation_reason'] = f"Merged into {keep_id}"
                    bullet['last_updated'] = datetime.now().isoformat()
                    break

        # Update merged content if provided
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
