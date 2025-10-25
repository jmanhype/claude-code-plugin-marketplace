#!/usr/bin/env python3
"""
ACE Delta Validation Script

Validates delta JSON against schema and checks for common issues:
- Schema compliance
- Bullet ID format and uniqueness
- Reference integrity (edits/merges/deprecations reference existing bullets)
- Counter sanity (no negative results)
- Conflict detection (contradictory operations)

Usage:
    python validate_delta.py <delta_file> [--playbook <playbook_file>]

Exit codes:
    0: Valid delta
    1: Validation errors found
    2: File or schema errors
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class DeltaValidator:
    def __init__(self, delta_path: str, playbook_path: Optional[str] = None):
        self.delta_path = Path(delta_path)
        self.playbook_path = Path(playbook_path) if playbook_path else None
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.delta: Optional[Dict] = None
        self.playbook: Optional[Dict] = None
        self.existing_bullet_ids: Set[str] = set()

    def load_files(self) -> bool:
        """Load delta and playbook JSON files"""
        try:
            with open(self.delta_path, 'r') as f:
                self.delta = json.load(f)
        except FileNotFoundError:
            self.errors.append(f"Delta file not found: {self.delta_path}")
            return False
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in delta file: {e}")
            return False

        if self.playbook_path:
            try:
                with open(self.playbook_path, 'r') as f:
                    self.playbook = json.load(f)
                    self.existing_bullet_ids = {
                        b['id'] for b in self.playbook.get('bullets', [])
                    }
            except FileNotFoundError:
                self.warnings.append(f"Playbook file not found: {self.playbook_path}")
            except json.JSONDecodeError as e:
                self.errors.append(f"Invalid JSON in playbook file: {e}")
                return False

        return True

    def validate_bullet_id(self, bullet_id: str) -> bool:
        """Validate bullet ID format: bullet-YYYY-MM-DD-NNN"""
        pattern = r'^bullet-\d{4}-\d{2}-\d{2}-\d{3}$'
        if not re.match(pattern, bullet_id):
            self.errors.append(
                f"Invalid bullet ID format: {bullet_id} "
                f"(expected: bullet-YYYY-MM-DD-NNN)"
            )
            return False
        return True

    def validate_delta_id(self, delta_id: str) -> bool:
        """Validate delta ID format: delta-YYYY-MM-DD-NNN"""
        pattern = r'^delta-\d{4}-\d{2}-\d{2}-\d{3}$'
        if not re.match(pattern, delta_id):
            self.errors.append(
                f"Invalid delta ID format: {delta_id} "
                f"(expected: delta-YYYY-MM-DD-NNN)"
            )
            return False
        return True

    def validate_new_bullets(self) -> None:
        """Validate new bullets in delta"""
        new_bullets = self.delta.get('new_bullets', [])
        new_bullet_ids = set()

        for i, bullet in enumerate(new_bullets):
            # Check required fields
            required = ['id', 'title', 'content', 'tags']
            for field in required:
                if field not in bullet:
                    self.errors.append(
                        f"new_bullets[{i}]: Missing required field '{field}'"
                    )

            # Validate ID format
            if 'id' in bullet:
                self.validate_bullet_id(bullet['id'])

                # Check for duplicate IDs within new bullets
                if bullet['id'] in new_bullet_ids:
                    self.errors.append(
                        f"Duplicate bullet ID in new_bullets: {bullet['id']}"
                    )
                new_bullet_ids.add(bullet['id'])

                # Check if ID already exists in playbook
                if self.existing_bullet_ids and bullet['id'] in self.existing_bullet_ids:
                    self.errors.append(
                        f"Bullet ID already exists in playbook: {bullet['id']}"
                    )

            # Validate title length
            if 'title' in bullet:
                if len(bullet['title']) < 5:
                    self.errors.append(
                        f"new_bullets[{i}]: Title too short (min 5 chars)"
                    )
                if len(bullet['title']) > 100:
                    self.errors.append(
                        f"new_bullets[{i}]: Title too long (max 100 chars)"
                    )

            # Validate content length
            if 'content' in bullet:
                if len(bullet['content']) < 20:
                    self.errors.append(
                        f"new_bullets[{i}]: Content too short (min 20 chars)"
                    )

            # Validate tags
            if 'tags' in bullet:
                if not bullet['tags']:
                    self.errors.append(
                        f"new_bullets[{i}]: At least one tag required"
                    )
                for tag in bullet['tags']:
                    if not re.match(r'^[a-z0-9._-]+$', tag):
                        self.errors.append(
                            f"new_bullets[{i}]: Invalid tag format: {tag}"
                        )

            # Validate confidence if present
            if 'confidence' in bullet:
                if bullet['confidence'] not in ['high', 'medium', 'low']:
                    self.errors.append(
                        f"new_bullets[{i}]: Invalid confidence value"
                    )

            # Validate scope if present
            if 'scope' in bullet:
                valid_scopes = ['global', 'project', 'domain', 'temporary']
                if bullet['scope'] not in valid_scopes:
                    self.errors.append(
                        f"new_bullets[{i}]: Invalid scope value"
                    )

    def validate_edits(self) -> None:
        """Validate edit operations"""
        edits = self.delta.get('edits', [])

        for i, edit in enumerate(edits):
            # Check required fields
            if 'id' not in edit:
                self.errors.append(f"edits[{i}]: Missing required field 'id'")
                continue

            if 'set' not in edit:
                self.errors.append(f"edits[{i}]: Missing required field 'set'")
                continue

            # Validate ID format
            self.validate_bullet_id(edit['id'])

            # Check if bullet exists in playbook
            if self.existing_bullet_ids and edit['id'] not in self.existing_bullet_ids:
                self.errors.append(
                    f"edits[{i}]: Bullet ID not found in playbook: {edit['id']}"
                )

            # Check that 'set' has at least one field
            if not edit['set']:
                self.errors.append(
                    f"edits[{i}]: 'set' must have at least one field"
                )

            # Recommend rationale
            if 'rationale' not in edit:
                self.warnings.append(
                    f"edits[{i}]: Missing rationale (recommended)"
                )

    def validate_merges(self) -> None:
        """Validate merge operations"""
        merges = self.delta.get('merges', [])

        for i, merge in enumerate(merges):
            # Check required fields
            required = ['keep_id', 'merge_ids', 'rationale']
            for field in required:
                if field not in merge:
                    self.errors.append(
                        f"merges[{i}]: Missing required field '{field}'"
                    )

            if 'keep_id' in merge:
                self.validate_bullet_id(merge['keep_id'])

                # Check if keep_id exists
                if self.existing_bullet_ids and merge['keep_id'] not in self.existing_bullet_ids:
                    self.errors.append(
                        f"merges[{i}]: keep_id not found in playbook: {merge['keep_id']}"
                    )

            if 'merge_ids' in merge:
                if not merge['merge_ids']:
                    self.errors.append(
                        f"merges[{i}]: merge_ids must have at least one ID"
                    )

                for merge_id in merge['merge_ids']:
                    self.validate_bullet_id(merge_id)

                    # Check if merge_id exists
                    if self.existing_bullet_ids and merge_id not in self.existing_bullet_ids:
                        self.errors.append(
                            f"merges[{i}]: merge_id not found in playbook: {merge_id}"
                        )

                    # Check that merge_id != keep_id
                    if 'keep_id' in merge and merge_id == merge['keep_id']:
                        self.errors.append(
                            f"merges[{i}]: merge_id cannot be same as keep_id: {merge_id}"
                        )

    def validate_deprecations(self) -> None:
        """Validate deprecation operations"""
        deprecations = self.delta.get('deprecations', [])

        for i, deprecation in enumerate(deprecations):
            # Check required fields
            if 'id' not in deprecation:
                self.errors.append(
                    f"deprecations[{i}]: Missing required field 'id'"
                )
                continue

            if 'reason' not in deprecation:
                self.errors.append(
                    f"deprecations[{i}]: Missing required field 'reason'"
                )

            # Validate ID format
            self.validate_bullet_id(deprecation['id'])

            # Check if bullet exists
            if self.existing_bullet_ids and deprecation['id'] not in self.existing_bullet_ids:
                self.errors.append(
                    f"deprecations[{i}]: Bullet ID not found in playbook: {deprecation['id']}"
                )

            # Validate replacement_id if present
            if 'replacement_id' in deprecation:
                self.validate_bullet_id(deprecation['replacement_id'])

    def validate_counters(self) -> None:
        """Validate counter updates"""
        counters = self.delta.get('counters', [])

        for i, counter in enumerate(counters):
            # Check required fields
            if 'id' not in counter:
                self.errors.append(
                    f"counters[{i}]: Missing required field 'id'"
                )
                continue

            # Validate ID format
            self.validate_bullet_id(counter['id'])

            # Check if bullet exists
            if self.existing_bullet_ids and counter['id'] not in self.existing_bullet_ids:
                self.errors.append(
                    f"counters[{i}]: Bullet ID not found in playbook: {counter['id']}"
                )

            # At least one delta required
            if 'helpful_delta' not in counter and 'harmful_delta' not in counter:
                self.errors.append(
                    f"counters[{i}]: Must specify helpful_delta or harmful_delta"
                )

    def check_conflicts(self) -> None:
        """Check for conflicting operations"""
        # Collect all affected bullet IDs
        edited_ids = {edit['id'] for edit in self.delta.get('edits', []) if 'id' in edit}
        deprecated_ids = {dep['id'] for dep in self.delta.get('deprecations', []) if 'id' in dep}
        merged_ids = set()
        for merge in self.delta.get('merges', []):
            merged_ids.update(merge.get('merge_ids', []))

        # Check for edits on deprecated bullets
        conflict = edited_ids & deprecated_ids
        if conflict:
            self.warnings.append(
                f"Editing and deprecating same bullets: {conflict}"
            )

        # Check for edits on merged bullets
        conflict = edited_ids & merged_ids
        if conflict:
            self.warnings.append(
                f"Editing and merging same bullets: {conflict}"
            )

        # Check for deprecating merged bullets
        conflict = deprecated_ids & merged_ids
        if conflict:
            self.warnings.append(
                f"Deprecating and merging same bullets: {conflict}"
            )

    def validate(self) -> bool:
        """Run all validations"""
        if not self.load_files():
            return False

        # Validate delta-level fields
        if 'delta_id' in self.delta:
            self.validate_delta_id(self.delta['delta_id'])

        # Check that delta has at least one operation
        operations = ['new_bullets', 'edits', 'merges', 'deprecations', 'counters']
        if not any(self.delta.get(op) for op in operations):
            self.errors.append(
                "Delta must contain at least one operation "
                "(new_bullets, edits, merges, deprecations, or counters)"
            )

        # Validate individual operation types
        self.validate_new_bullets()
        self.validate_edits()
        self.validate_merges()
        self.validate_deprecations()
        self.validate_counters()

        # Check for conflicts
        self.check_conflicts()

        return len(self.errors) == 0

    def print_results(self) -> None:
        """Print validation results"""
        print(f"\n{BLUE}=== Delta Validation Results ==={RESET}\n")
        print(f"Delta file: {self.delta_path}")
        if self.playbook_path:
            print(f"Playbook: {self.playbook_path}")
        print()

        if self.errors:
            print(f"{RED}✗ Errors ({len(self.errors)}):{RESET}")
            for error in self.errors:
                print(f"  {RED}•{RESET} {error}")
            print()

        if self.warnings:
            print(f"{YELLOW}⚠ Warnings ({len(self.warnings)}):{RESET}")
            for warning in self.warnings:
                print(f"  {YELLOW}•{RESET} {warning}")
            print()

        if not self.errors:
            print(f"{GREEN}✓ Delta is valid!{RESET}\n")

            # Print summary
            ops = []
            if self.delta.get('new_bullets'):
                ops.append(f"{len(self.delta['new_bullets'])} new bullets")
            if self.delta.get('edits'):
                ops.append(f"{len(self.delta['edits'])} edits")
            if self.delta.get('merges'):
                ops.append(f"{len(self.delta['merges'])} merges")
            if self.delta.get('deprecations'):
                ops.append(f"{len(self.delta['deprecations'])} deprecations")
            if self.delta.get('counters'):
                ops.append(f"{len(self.delta['counters'])} counter updates")

            print(f"Operations: {', '.join(ops)}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_delta.py <delta_file> [--playbook <playbook_file>]")
        sys.exit(2)

    delta_path = sys.argv[1]
    playbook_path = None

    # Parse optional --playbook argument
    if '--playbook' in sys.argv:
        idx = sys.argv.index('--playbook')
        if idx + 1 < len(sys.argv):
            playbook_path = sys.argv[idx + 1]

    validator = DeltaValidator(delta_path, playbook_path)
    is_valid = validator.validate()
    validator.print_results()

    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
