"""
Reflexion-based AppWorld executor.

Uses Claude Code session for code generation with iterative refinement.
Implements the Reflexion pattern: Generate → Execute → Analyze Error → Refine → Retry
"""

import os
import sys
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path

from .appworld_executor import AppWorldExecutor, APPWORLD_AVAILABLE


class ReflexionExecutor(AppWorldExecutor):
    """
    AppWorld executor with Reflexion-based code generation.

    Key differences from AppWorldExecutor:
    1. Uses Claude Code for code generation (not templates)
    2. Implements reflexion loop (retry with error feedback)
    3. Tracks refinement attempts and success patterns
    """

    def __init__(
        self,
        experiment_name: str = "ace_reflexion",
        max_attempts: int = 3,
        code_generator=None
    ):
        """
        Initialize Reflexion executor.

        Args:
            experiment_name: Name for tracking experiments
            max_attempts: Maximum refinement attempts per task (default: 3)
            code_generator: Callable that generates code (Claude Code session)
        """
        super().__init__(experiment_name=experiment_name)

        self.max_attempts = max_attempts
        self.code_generator = code_generator

        # Track reflexion statistics
        self.reflexion_stats = {
            'total_tasks': 0,
            'success_on_attempt': {i: 0 for i in range(1, max_attempts + 1)},
            'total_attempts': 0,
            'error_types': {},
            'refinement_patterns': []
        }

    def solve_task(
        self,
        instruction: str,
        apps: List[str],
        apis: List[Dict],
        playbook_bullets: List[Dict],
        ground_truth: str = None,
        task_id: str = None
    ) -> Dict[str, Any]:
        """
        Solve task using Reflexion pattern: generate, execute, refine on failure.

        Returns:
            {
                'code': final generated code,
                'final_answer': execution result,
                'success': bool,
                'tgc': Task Goal Completion,
                'sgc': Scenario Goal Completion,
                'attempts': number of attempts needed,
                'refinement_history': list of (code, error, tgc) tuples,
                'used_bullet_ids': [...],
                'bullet_feedback': {...}
            }
        """
        if not task_id:
            raise ValueError("task_id is required for AppWorld execution")

        # Extract strategies from bullets
        strategies = self._extract_strategies(playbook_bullets)
        used_bullet_ids = [b['id'] for b in playbook_bullets]

        # Track refinement history
        refinement_history = []

        # Reflexion loop: up to max_attempts
        for attempt in range(1, self.max_attempts + 1):
            print(f"\n{'='*70}")
            print(f"ATTEMPT {attempt}/{self.max_attempts}")
            print(f"{'='*70}")

            # Prepare generation context
            generation_context = {
                'instruction': instruction,
                'apps': apps,
                'apis': apis,
                'strategies': strategies,
                'bullets': playbook_bullets,
                'attempt': attempt,
                'previous_code': refinement_history[-1]['code'] if refinement_history else None,
                'previous_error': refinement_history[-1]['error'] if refinement_history else None,
                'previous_tgc': refinement_history[-1]['tgc'] if refinement_history else None
            }

            # Generate code (via Claude Code or fallback to template)
            if self.code_generator is not None:
                # Use Claude Code for generation
                code = self.code_generator(generation_context)
            else:
                # Fallback to template-based generation
                code = self._generate_code_with_bullets(
                    instruction, apps, apis, strategies, playbook_bullets
                )

            print(f"\n📝 Generated code ({len(code.split(chr(10)))} lines)")

            # Execute in AppWorld
            execution_result, success, tgc, sgc = self._execute_in_appworld(task_id, code)

            print(f"\n📊 Execution result:")
            print(f"   TGC: {tgc:.2f}")
            print(f"   SGC: {sgc:.2f}")
            print(f"   Success: {success}")

            # Track attempt
            refinement_history.append({
                'attempt': attempt,
                'code': code,
                'error': execution_result if not success else None,
                'tgc': tgc,
                'sgc': sgc,
                'success': success
            })

            # Success! Exit reflexion loop
            if success:
                print(f"\n✅ Task succeeded on attempt {attempt}")
                self.reflexion_stats['success_on_attempt'][attempt] += 1
                break

            # Failed - analyze for next attempt
            if attempt < self.max_attempts:
                print(f"\n❌ Attempt {attempt} failed, will refine...")
                print(f"   Error: {execution_result[:200]}")

                # Track error type
                error_type = self._classify_error(execution_result)
                self.reflexion_stats['error_types'][error_type] = \
                    self.reflexion_stats['error_types'].get(error_type, 0) + 1
            else:
                print(f"\n❌ All {self.max_attempts} attempts exhausted")

        # Update statistics
        self.reflexion_stats['total_tasks'] += 1
        self.reflexion_stats['total_attempts'] += len(refinement_history)

        # Determine bullet feedback
        bullet_feedback = self._evaluate_bullet_effectiveness(
            playbook_bullets, success, execution_result
        )

        # Compile result
        result = {
            'code': refinement_history[-1]['code'],
            'final_answer': execution_result,
            'used_bullet_ids': used_bullet_ids,
            'bullet_feedback': bullet_feedback,
            'success': success,
            'tgc': tgc,
            'sgc': sgc,
            'strategies_applied': strategies,
            'attempts': len(refinement_history),
            'refinement_history': refinement_history,
            'task_id': task_id
        }

        # Store in execution history
        self.execution_history.append({
            'task_id': task_id,
            'instruction': instruction,
            'success': success,
            'tgc': tgc,
            'sgc': sgc,
            'attempts': len(refinement_history)
        })

        return result

    def _classify_error(self, error_message: str) -> str:
        """
        Classify error type for tracking.

        Args:
            error_message: Error message from execution

        Returns:
            Error type category
        """
        error_lower = error_message.lower()

        if 'attributeerror' in error_lower:
            return 'attribute_error'
        elif 'keyerror' in error_lower:
            return 'key_error'
        elif 'typeerror' in error_lower:
            return 'type_error'
        elif 'nameerror' in error_lower:
            return 'name_error'
        elif 'execution error' in error_lower:
            return 'execution_error'
        elif 'evaluation error' in error_lower:
            return 'evaluation_error'
        elif 'api' in error_lower or 'endpoint' in error_lower:
            return 'api_error'
        else:
            return 'other'

    def get_reflexion_stats(self) -> Dict[str, Any]:
        """Get reflexion statistics."""
        stats = self.reflexion_stats.copy()

        # Calculate success rate by attempt
        total = stats['total_tasks']
        if total > 0:
            stats['success_rate_by_attempt'] = {
                attempt: count / total
                for attempt, count in stats['success_on_attempt'].items()
            }
            stats['overall_success_rate'] = sum(
                stats['success_on_attempt'].values()
            ) / total
            stats['avg_attempts'] = stats['total_attempts'] / total

        return stats

    def print_reflexion_summary(self):
        """Print reflexion statistics summary."""
        stats = self.get_reflexion_stats()

        print("\n" + "="*70)
        print("REFLEXION STATISTICS")
        print("="*70)

        print(f"\n📊 Overall Metrics:")
        print(f"   Total tasks: {stats['total_tasks']}")
        print(f"   Overall success rate: {stats.get('overall_success_rate', 0):.1%}")
        print(f"   Average attempts: {stats.get('avg_attempts', 0):.2f}")

        print(f"\n📈 Success by Attempt:")
        for attempt in range(1, self.max_attempts + 1):
            count = stats['success_on_attempt'][attempt]
            rate = stats.get('success_rate_by_attempt', {}).get(attempt, 0)
            print(f"   Attempt {attempt}: {count} tasks ({rate:.1%})")

        print(f"\n🐛 Error Types:")
        for error_type, count in sorted(
            stats['error_types'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            print(f"   {error_type}: {count}")

        print("="*70)
