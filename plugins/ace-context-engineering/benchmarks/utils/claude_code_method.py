"""
Claude Code ACE Method: Full Generator → Reflector → Curator implementation.

This is the REAL ACE implementation based on the paper, replacing the
pattern-matching approach with bullet-driven adaptation.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from .base_method import AdaptiveMethod
from .bullet_retriever import BulletRetriever
from .skills_executor import SkillsExecutor
from .reflector import Reflector
from .curator_staged import StagedCurator


class ClaudeCodeACE(AdaptiveMethod):
    """
    ACE method implementation using Claude Code Skills.

    Workflow:
    1. GENERATE: Retrieve bullets → Generate solution → Track feedback
    2. REFLECT: Analyze outcome → Propose delta
    3. CURATE: Validate delta → Merge into playbook
    4. ADAPT: Iterate over training data with multi-epoch learning
    """

    def __init__(
        self,
        playbook_path: str,
        name: str = "ClaudeCodeACE",
        use_faiss: bool = True,
        executor=None
    ):
        super().__init__(name)

        self.playbook_path = Path(playbook_path)
        self.load_playbook(str(self.playbook_path))

        # Initialize components
        self.retriever = BulletRetriever(str(self.playbook_path))
        # Allow custom executor (e.g., AppWorldExecutor), default to mock
        self.executor = executor if executor is not None else SkillsExecutor()
        self.reflector = Reflector()
        # Use new three-stage curator with FAISS-based deduplication
        self.curator = StagedCurator(str(self.playbook_path), use_faiss=use_faiss)

        # Track evolution
        self.epoch_snapshots = []

    def generate(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate solution using bullet guidance.

        This is the KEY difference from pattern matching:
        - Retrieves relevant bullets
        - Passes them to executor
        - Executor ACTUALLY USES them (not ignores them!)
        - Tracks which bullets helped/harmed
        """
        instruction = sample.get('instruction', '')
        apps = sample.get('apps', [])
        apis = sample.get('apis', [])

        # Extract tags from sample for better retrieval
        tags = self._extract_tags(sample)

        # Retrieve relevant bullets
        print(f"\n🔍 Retrieving bullets for: {instruction[:80]}...")
        results = self.retriever.retrieve(query=instruction, tags=tags, top_k=5)

        print(f"   Retrieved {len(results)} bullets:")
        for r in results:
            print(f"   - [{r.score:.2f}] {r.title}")

        # Convert to dict format for executor
        playbook_bullets = [r.to_dict() for r in results]
        for i, bullet in enumerate(playbook_bullets):
            # Add full content from retriever
            bullet['content'] = results[i].content

        # Generate solution using bullets
        print(f"\n⚙️  Generating solution with bullet guidance...")
        execution_result = self.executor.solve_task(
            instruction=instruction,
            apps=apps,
            apis=apis,
            playbook_bullets=playbook_bullets,
            ground_truth=sample.get('ground_truth'),
            task_id=sample.get('task_id') or sample.get('id')
        )

        print(f"   Success: {execution_result['success']}")
        print(f"   Used {len(execution_result['used_bullet_ids'])} bullets")
        print(f"   Feedback: {execution_result['bullet_feedback']}")

        # Update metrics
        self.metrics['total_tasks'] += 1
        if execution_result['success']:
            self.metrics['successful_tasks'] += 1

        # CRITICAL FIX: Store the FULL execution_result for reflection
        # This includes execution_feedback with error_analysis!
        self._last_execution_result = execution_result

        return {
            'prediction': execution_result['code'],
            'used_bullet_ids': execution_result['used_bullet_ids'],
            'bullet_feedback': execution_result['bullet_feedback'],
            'observations': execution_result.get('strategies_applied', []),
            'execution_result': execution_result
        }

    def reflect(
        self,
        sample: Dict,
        prediction: str,
        ground_truth: str,
        success: bool
    ) -> Dict:
        """
        Reflect on outcome and propose delta.

        This ACTUALLY analyzes errors and proposes meaningful updates,
        unlike the no-op version in the old implementation.
        """
        print(f"\n🤔 Reflecting on task outcome...")

        # CRITICAL FIX: Get the FULL execution result from last generate() call
        # Don't recreate it - that discards execution_feedback with error_analysis!
        execution_result = getattr(self, '_last_execution_result', {
            'success': success,
            'bullet_feedback': getattr(self, '_last_bullet_feedback', {}),
            'strategies_applied': getattr(self, '_last_strategies', [])
        })

        # Retrieve the bullets that were used
        retrieved_bullets = []
        if hasattr(self, '_last_retrieved_bullets'):
            retrieved_bullets = self._last_retrieved_bullets

        # Analyze and propose delta
        delta = self.reflector.reflect(
            sample=sample,
            prediction=prediction,
            ground_truth=ground_truth,
            execution_result=execution_result,
            retrieved_bullets=retrieved_bullets
        )

        print(f"   Error type: {delta.get('error_type', 'none')}")
        print(f"   Proposed {len(delta.get('new_bullets', []))} new bullet(s)")
        print(f"   Proposed {len(delta.get('counters', []))} counter update(s)")

        return delta

    def curate(self, delta: Dict) -> Dict:
        """
        Validate and merge delta.

        This ACTUALLY checks for duplicates and merges deltas,
        unlike the stub in the old implementation.
        """
        # Validate and normalize using three-stage curator
        curation_result = self.curator.curate_delta(delta)

        # Merge if passed all quality gates
        if curation_result.passed and not curation_result.requires_human_review:
            clean_delta = curation_result.clean_delta
            success = self.curator.merge_delta(clean_delta)

            if success:
                # Update metrics
                self.metrics['bullets_added'] += len(clean_delta.get('new_bullets', []))
                self.metrics['bullets_updated'] += len(clean_delta.get('counters', []))

                # Reload playbook
                self.playbook = self.curator.playbook
                self.retriever = BulletRetriever(str(self.playbook_path))
            else:
                print(f"   ❌ Delta merge failed")
        else:
            if not curation_result.passed:
                print(f"   ❌ Delta did not pass quality gates")
            elif curation_result.requires_human_review:
                print(f"   ⚠️  Delta requires human review, skipping merge")

        return curation_result

    def _adapt_offline(self, samples: List[Dict], max_epochs: int) -> Dict:
        """
        REAL offline adaptation with multi-epoch training.

        This is the full ACE loop that was missing in the old implementation.

        For each epoch:
            For each sample:
                1. Generate solution with current playbook
                2. Reflect on outcome
                3. Curate and merge delta
            Apply grow-and-refine (deduplication)
            Save epoch snapshot
        """
        print(f"\n{'='*80}")
        print(f"OFFLINE ADAPTATION: {len(samples)} samples, {max_epochs} epochs")
        print(f"{'='*80}\n")

        results = {
            'epochs': [],
            'final_metrics': None
        }

        for epoch in range(max_epochs):
            print(f"\n{'─'*80}")
            print(f"EPOCH {epoch + 1}/{max_epochs}")
            print(f"{'─'*80}")

            epoch_metrics = {
                'epoch': epoch + 1,
                'successes': 0,
                'failures': 0,
                'bullets_added': 0,
                'bullets_updated': 0
            }

            # Process each sample
            for i, sample in enumerate(samples):
                print(f"\n[Sample {i+1}/{len(samples)}] {sample.get('id', 'unknown')}")

                # 1. GENERATE
                generation_result = self.generate(sample)
                prediction = generation_result['prediction']
                success = generation_result['execution_result']['success']

                # Store for reflection
                self._last_retrieved_bullets = [
                    self.retriever.get_bullet(bid)
                    for bid in generation_result['used_bullet_ids']
                ]
                self._last_retrieved_bullets = [b for b in self._last_retrieved_bullets if b]
                self._last_bullet_feedback = generation_result.get('bullet_feedback', {})
                self._last_strategies = generation_result.get('observations', [])

                # Track success
                if success:
                    epoch_metrics['successes'] += 1
                else:
                    epoch_metrics['failures'] += 1

                # 2. REFLECT
                delta = self.reflect(
                    sample=sample,
                    prediction=prediction,
                    ground_truth=sample.get('ground_truth', ''),
                    success=success
                )

                # 3. CURATE
                curation_result = self.curate(delta)

                # Track metrics
                if curation_result.passed and curation_result.clean_delta:
                    clean_delta = curation_result.clean_delta
                    epoch_metrics['bullets_added'] += len(clean_delta.get('new_bullets', []))
                    epoch_metrics['bullets_updated'] += len(clean_delta.get('counters', []))

            # Calculate epoch success rate
            total = epoch_metrics['successes'] + epoch_metrics['failures']
            epoch_metrics['success_rate'] = epoch_metrics['successes'] / total if total > 0 else 0.0

            print(f"\n📊 Epoch {epoch + 1} Summary:")
            print(f"   Success rate: {epoch_metrics['success_rate']:.1%}")
            print(f"   Bullets added: {epoch_metrics['bullets_added']}")
            print(f"   Bullets updated: {epoch_metrics['bullets_updated']}")

            results['epochs'].append(epoch_metrics)

            # Save snapshot
            self._save_epoch_snapshot(epoch + 1)

            # Grow-and-refine (deduplication) at end of epoch
            if epoch < max_epochs - 1:  # Not on last epoch
                self._apply_grow_and_refine()

        results['final_metrics'] = self.get_metrics()

        print(f"\n{'='*80}")
        print(f"OFFLINE ADAPTATION COMPLETE")
        print(f"{'='*80}")
        print(f"Final success rate: {results['epochs'][-1]['success_rate']:.1%}")
        print(f"Total bullets added: {sum(e['bullets_added'] for e in results['epochs'])}")
        print(f"Total bullets updated: {sum(e['bullets_updated'] for e in results['epochs'])}")
        print(f"{'='*80}\n")

        return results

    def _adapt_online(self, samples: List[Dict]) -> Dict:
        """
        Online adaptation: Sequential test-time learning.

        Similar to offline but processes samples once in order.
        """
        print(f"\n{'='*80}")
        print(f"ONLINE ADAPTATION: {len(samples)} samples")
        print(f"{'='*80}\n")

        results = {
            'samples': [],
            'final_metrics': None
        }

        for i, sample in enumerate(samples):
            print(f"\n[Sample {i+1}/{len(samples)}] {sample.get('id', 'unknown')}")

            # Generate → Reflect → Curate
            generation_result = self.generate(sample)
            prediction = generation_result['prediction']
            success = generation_result['execution_result']['success']

            self._last_retrieved_bullets = [
                self.retriever.get_bullet(bid)
                for bid in generation_result['used_bullet_ids']
            ]
            self._last_retrieved_bullets = [b for b in self._last_retrieved_bullets if b]
            self._last_bullet_feedback = generation_result.get('bullet_feedback', {})
            self._last_strategies = generation_result.get('observations', [])

            delta = self.reflect(
                sample=sample,
                prediction=prediction,
                ground_truth=sample.get('ground_truth', ''),
                success=success
            )

            curation_result = self.curate(delta)

            results['samples'].append({
                'id': sample.get('id'),
                'success': success,
                'delta_merged': curation_result.passed and curation_result.clean_delta is not None
            })

        results['final_metrics'] = self.get_metrics()

        print(f"\n{'='*80}")
        print(f"ONLINE ADAPTATION COMPLETE")
        print(f"{'='*80}\n")

        return results

    def _extract_tags(self, sample: Dict) -> List[str]:
        """Extract relevant tags from sample for retrieval."""
        tags = []
        instruction = sample.get('instruction', '').lower()

        # Map keywords to tags
        tag_map = {
            'slack': ['api.slack', 'messaging'],
            'venmo': ['api.venmo', 'payment'],
            'email': ['api.email', 'gmail'],
            'send': ['send', 'post'],
            'fetch': ['fetch', 'get'],
            'delete': ['delete', 'remove'],
            'validate': ['validation'],
            'filter': ['filter'],
            'pagination': ['pagination'],
        }

        for keyword, keyword_tags in tag_map.items():
            if keyword in instruction:
                tags.extend(keyword_tags)

        return list(set(tags))

    def _save_epoch_snapshot(self, epoch: int):
        """Save playbook snapshot after epoch."""
        snapshot_path = self.playbook_path.parent / f"playbook_epoch_{epoch}.json"

        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(self.playbook, f, indent=2)

        self.epoch_snapshots.append({
            'epoch': epoch,
            'path': str(snapshot_path),
            'timestamp': datetime.now().isoformat(),
            'num_bullets': len(self.playbook.get('bullets', []))
        })

        print(f"   💾 Saved epoch {epoch} snapshot: {snapshot_path.name}")

    def _apply_grow_and_refine(self):
        """
        Apply grow-and-refine mechanism (Section 3.2).

        Deduplicate bullets using embeddings/TF-IDF.
        """
        print(f"\n🌱 Applying grow-and-refine (deduplication)...")

        bullets = self.playbook.get('bullets', [])
        active_bullets = [b for b in bullets if b.get('status') == 'active']

        print(f"   Active bullets before: {len(active_bullets)}")

        # Find duplicates
        duplicates = self.curator.deduplicator.find_duplicates(bullets, threshold=0.85)

        if duplicates:
            print(f"   Found {len(duplicates)} duplicate pair(s)")

            # Propose merges
            merges = self.curator.deduplicator.propose_merges(bullets, duplicates)

            print(f"   Proposed {len(merges)} merge operation(s)")

            # Apply merges
            for merge in merges:
                self.curator._apply_merge(merge)

            # Save updated playbook
            self.curator._save_playbook()

            # Reload
            self.playbook = self.curator.playbook
            self.retriever = BulletRetriever(str(self.playbook_path))

            active_after = sum(1 for b in self.playbook.get('bullets', []) if b.get('status') == 'active')
            print(f"   Active bullets after: {active_after} (removed {len(active_bullets) - active_after})")
        else:
            print(f"   No duplicates found")
