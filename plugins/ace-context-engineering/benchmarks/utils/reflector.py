"""
Reflector: Analyzes task outcomes and proposes delta updates.

Based on ACE paper Section 3 and Appendix D Figure 10.
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional


class Reflector:
    """
    Reflects on task execution to identify:
    - What worked (helpful bullets)
    - What didn't work (harmful bullets, missing guidance)
    - What should be added/edited (new bullets, counter updates)
    """

    def __init__(self):
        self.reflection_history = []

    def reflect(
        self,
        sample: Dict[str, Any],
        prediction: str,
        ground_truth: Optional[str],
        execution_result: Dict[str, Any],
        retrieved_bullets: List[Dict]
    ) -> Dict[str, Any]:
        """
        Analyze task outcome and propose delta.

        Args:
            sample: Original task sample
            prediction: Generated solution code
            ground_truth: Expected answer (if available)
            execution_result: Result from SkillsExecutor with bullet feedback
            retrieved_bullets: Bullets that were retrieved for this task

        Returns:
            Delta proposal with new_bullets, counters, edits, etc.
        """
        success = execution_result.get('success', False)
        bullet_feedback = execution_result.get('bullet_feedback', {})

        # Analyze what went wrong or right
        error_analysis = self._analyze_outcome(
            sample, prediction, ground_truth, success, execution_result
        )

        # Identify missing guidance
        missing_guidance = self._identify_missing_guidance(
            sample, prediction, error_analysis, retrieved_bullets
        )

        # Propose counter updates
        counters = self._propose_counter_updates(bullet_feedback, success)

        # Propose new bullets if gaps identified
        new_bullets = self._propose_new_bullets(
            sample, error_analysis, missing_guidance, success
        )

        # Construct delta
        delta = {
            'new_bullets': new_bullets,
            'counters': counters,
            'edits': [],
            'merges': [],
            'deprecations': [],
            'reasoning': error_analysis['reasoning'],
            'error_type': error_analysis.get('error_type'),
            'root_cause': error_analysis.get('root_cause'),
        }

        # Store reflection
        self.reflection_history.append({
            'task_id': sample.get('id', 'unknown'),
            'success': success,
            'delta': delta,
            'timestamp': datetime.now().isoformat()
        })

        return delta

    def _analyze_outcome(
        self,
        sample: Dict,
        prediction: str,
        ground_truth: Optional[str],
        success: bool,
        execution_result: Dict
    ) -> Dict[str, str]:
        """
        Analyze task outcome to identify error types and root causes.

        Now enhanced to use rich error_analysis from AppWorldExecutor when available.

        Error types (from paper):
        - wrong_source: Used wrong API endpoint
        - bad_filters: Incorrect query filters
        - incomplete_pagination: Didn't fetch all pages
        - logic_error: Incorrect business logic
        - validation_missing: No input validation

        AppWorld-specific error types:
        - api_misuse: Incorrect API method names
        - authentication_error: Missing login/auth
        - missing_data: Incorrect response parsing
        """
        analysis = {
            'reasoning': '',
            'error_type': None,
            'root_cause': None,
            'correct_approach': None,
            'error_messages': [],
            'failed_apis': [],
            'missing_patterns': [],
            'suggested_fixes': []
        }

        instruction = sample.get('instruction', '')

        if success:
            analysis['reasoning'] = (
                f"Task completed successfully. Instruction: {instruction[:100]}. "
                f"The generated code executed without errors and produced expected output."
            )
            analysis['correct_approach'] = prediction
            return analysis

        # PRIORITY 1: Check for AppWorldExecutor error_analysis
        execution_feedback = execution_result.get('execution_feedback', {})
        error_analysis = execution_feedback.get('error_analysis', {})

        print(f"\n🔍 DEBUG Reflector._analyze_outcome:")
        print(f"   execution_feedback keys: {list(execution_feedback.keys())}")
        print(f"   error_analysis: {error_analysis}")
        print(f"   error_analysis type: {type(error_analysis)}")
        if isinstance(error_analysis, dict):
            print(f"   error_analysis.get('error_type'): {error_analysis.get('error_type')}")
            print(f"   error_analysis.get('missing_patterns'): {error_analysis.get('missing_patterns')}")
            print(f"   error_analysis.get('error_messages'): {error_analysis.get('error_messages')}")

        if error_analysis and error_analysis.get('error_type'):
            # Use rich error analysis from AppWorldExecutor
            analysis['error_type'] = error_analysis.get('error_type')
            analysis['error_messages'] = error_analysis.get('error_messages', [])
            analysis['failed_apis'] = error_analysis.get('failed_apis', [])
            analysis['missing_patterns'] = error_analysis.get('missing_patterns', [])
            analysis['suggested_fixes'] = error_analysis.get('suggested_fixes', [])

            # Build detailed root cause from error messages
            error_msgs = analysis['error_messages']
            if error_msgs:
                analysis['root_cause'] = error_msgs[0]  # Use first error as primary
            else:
                analysis['root_cause'] = f"Execution failed with {analysis['error_type']}"

            # Build correct approach from suggested fixes and missing patterns
            approaches = []
            if analysis['suggested_fixes']:
                approaches.extend(analysis['suggested_fixes'])
            if analysis['missing_patterns']:
                approaches.extend(analysis['missing_patterns'])
            analysis['correct_approach'] = '; '.join(approaches) if approaches else 'Review error messages and API documentation'

            analysis['reasoning'] = (
                f"Task failed with AppWorld error: {analysis['error_type']}. "
                f"Root cause: {analysis['root_cause']}. "
                f"Instruction: {instruction[:100]}. "
                f"Missing patterns: {analysis['missing_patterns']}. "
                f"Suggested fixes: {analysis['suggested_fixes']}."
            )

            return analysis

        # FALLBACK: Use pattern matching for backwards compatibility with SkillsExecutor
        code = prediction
        strategies = execution_result.get('strategies_applied', [])

        # Check for specific error patterns
        if 'pagination' in instruction.lower() and 'while' not in code:
            analysis['error_type'] = 'incomplete_pagination'
            analysis['root_cause'] = 'Did not implement pagination loop despite task requiring it'
            analysis['correct_approach'] = 'Should use while loop with cursor/offset'

        elif 'filter' in instruction.lower() and 'filter' not in code.lower():
            analysis['error_type'] = 'bad_filters'
            analysis['root_cause'] = 'Did not apply filtering logic mentioned in instruction'
            analysis['correct_approach'] = 'Should add filter conditions based on requirements'

        elif 'validate' in instruction.lower() and 'assert' not in code:
            analysis['error_type'] = 'validation_missing'
            analysis['root_cause'] = 'No input validation despite instruction mentioning it'
            analysis['correct_approach'] = 'Should add assert statements or validation checks'

        elif not any(api in code.lower() for api in ['client', 'api', 'request']):
            analysis['error_type'] = 'wrong_source'
            analysis['root_cause'] = 'Did not use appropriate API client or endpoint'
            analysis['correct_approach'] = 'Should identify correct API from available endpoints'

        else:
            analysis['error_type'] = 'logic_error'
            analysis['root_cause'] = 'General logic error in implementation'
            analysis['correct_approach'] = 'Review business logic and task requirements'

        analysis['reasoning'] = (
            f"Task failed with error type: {analysis['error_type']}. "
            f"Root cause: {analysis['root_cause']}. "
            f"Instruction was: {instruction[:100]}. "
            f"Applied strategies: {strategies}. "
        )

        return analysis

    def _identify_missing_guidance(
        self,
        sample: Dict,
        prediction: str,
        error_analysis: Dict,
        retrieved_bullets: List[Dict]
    ) -> List[str]:
        """
        Identify gaps in playbook guidance.

        Returns:
            List of missing guidance descriptions
        """
        missing = []
        error_type = error_analysis.get('error_type')

        # Check if we had bullets for this error type
        bullet_tags = set()
        for bullet in retrieved_bullets:
            bullet_tags.update(bullet.get('tags', []))

        # Map error types to expected tags
        expected_tags = {
            'incomplete_pagination': ['pagination', 'api.pagination'],
            'bad_filters': ['filter', 'query'],
            'validation_missing': ['validation', 'input_validation'],
            'wrong_source': ['api', 'endpoint'],
        }

        if error_type and error_type in expected_tags:
            for tag in expected_tags[error_type]:
                if tag not in bullet_tags:
                    missing.append(f"Missing guidance for: {tag}")

        # Check instruction keywords
        instruction_lower = sample.get('instruction', '').lower()
        if 'pagination' in instruction_lower and 'pagination' not in bullet_tags:
            missing.append("No pagination guidance available")

        if 'validate' in instruction_lower and 'validation' not in bullet_tags:
            missing.append("No validation guidance available")

        return missing

    def _propose_counter_updates(
        self,
        bullet_feedback: Dict[str, str],
        success: bool
    ) -> List[Dict]:
        """
        Propose counter updates based on bullet effectiveness.

        Args:
            bullet_feedback: {'bullet-id': 'helpful'|'harmful'|'neutral'}
            success: Whether task succeeded

        Returns:
            [{'id': 'bullet-123', 'helpful_delta': 1}, ...]
        """
        counters = []

        for bullet_id, feedback in bullet_feedback.items():
            if feedback == 'helpful':
                counters.append({
                    'id': bullet_id,
                    'helpful_delta': 1,
                    'harmful_delta': 0,
                    'evidence': {
                        'type': 'execution',
                        'ref': f'reflection-{datetime.now().isoformat()}',
                        'note': 'Bullet guidance was applied and task succeeded'
                    }
                })
            elif feedback == 'harmful':
                counters.append({
                    'id': bullet_id,
                    'helpful_delta': 0,
                    'harmful_delta': 1,
                    'evidence': {
                        'type': 'execution',
                        'ref': f'reflection-{datetime.now().isoformat()}',
                        'note': 'Bullet guidance led to incorrect solution'
                    }
                })

        return counters

    def _generate_appworld_bullet(
        self,
        sample: Dict,
        error_analysis: Dict
    ) -> Optional[Dict]:
        """
        Generate AppWorld-specific bullet from rich error analysis.

        Uses error_type, failed_apis, missing_patterns, and suggested_fixes
        to create domain-specific bullets.
        """
        error_type = error_analysis.get('error_type')
        missing_patterns = error_analysis.get('missing_patterns', [])
        suggested_fixes = error_analysis.get('suggested_fixes', [])
        failed_apis = error_analysis.get('failed_apis', [])

        print(f"\n🔍 DEBUG _generate_appworld_bullet:")
        print(f"   error_type={error_type}")
        print(f"   missing_patterns={missing_patterns}")
        print(f"   suggested_fixes={suggested_fixes}")
        print(f"   failed_apis={failed_apis}")

        if not error_type:
            print(f"   ❌ No error_type, returning None")
            return None

        # Extract app name from instruction or failed APIs
        instruction = sample.get('instruction', '')
        apps = sample.get('apps', [])
        app_name = apps[0] if apps else None

        # Generate unique bullet ID
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        bullet_id = f"bullet-{timestamp}"

        # Generate bullet based on error type
        if error_type == 'authentication_error':
            title = f"Always authenticate before using {app_name or 'app'} APIs"
            content = f"When using {app_name or 'app'} APIs, always call the login() method first to obtain an access token before making any other API calls. "
            if missing_patterns:
                content += f"Common mistake: {missing_patterns[0]}. "
            content += "Example: token = app.login(username, password); result = app.search(token, query)"
            tags = ['authentication', 'api', 'best_practice']
            if app_name:
                tags.append(f'app.{app_name}')

        elif error_type == 'api_misuse':
            title = f"Use correct API method names for {app_name or 'app'}"
            content = "API method names must match the available endpoints exactly. "
            if suggested_fixes:
                content += f"Tip: {suggested_fixes[0]}. "
            if failed_apis:
                content += f"Failed APIs: {', '.join(failed_apis)}. "
            content += "Check API documentation for correct method names (e.g., search_tracks not get_tracks)."
            tags = ['api', 'method_names', 'debugging']
            if app_name:
                tags.append(f'app.{app_name}')

        elif error_type == 'missing_data':
            title = "Check API response structure before accessing nested fields"
            content = "Always verify that API response contains expected fields before accessing them to avoid NoneType errors. "
            if missing_patterns:
                content += f"Common issue: {missing_patterns[0]}. "
            content += "Use .get() method for safe access: data.get('field', default_value) or check 'if key in dict' first."
            tags = ['api', 'error_handling', 'data_parsing', 'best_practice']
            if app_name:
                tags.append(f'app.{app_name}')

        elif error_type == 'logic_error':
            print(f"   📍 Handling logic_error...")
            # For logic errors, extract patterns from missing_patterns
            # Don't require missing_patterns - use error context instead
            if missing_patterns:
                print(f"   ✅ Has missing_patterns, creating specific bullet")
                title = f"Verify {app_name or 'app'} API logic and requirements"
                content = f"When implementing {app_name or 'app'} operations: "
                content += '; '.join(missing_patterns)
                if suggested_fixes:
                    content += f". Suggested approach: {'; '.join(suggested_fixes)}"
            else:
                print(f"   ⚠️  No missing_patterns, creating generic bullet")
                # Generic logic error bullet from instruction context
                title = f"Review {app_name or 'task'} implementation logic"
                content = f"Task instruction: {instruction[:150]}. Review implementation to ensure all requirements are met."
                if suggested_fixes:
                    content += f" Suggested fixes: {'; '.join(suggested_fixes)}"

            tags = ['logic', 'debugging', 'api']
            if app_name:
                tags.append(f'app.{app_name}')
            print(f"   ✅ Generated bullet with title: {title[:50]}...")

        else:
            # Unknown error type, try to build generic bullet from patterns
            if not missing_patterns and not suggested_fixes:
                return None

            title = f"Handle {error_type} when using {app_name or 'app'}"
            content = ""
            if missing_patterns:
                content += f"Missing: {'; '.join(missing_patterns)}. "
            if suggested_fixes:
                content += f"Fix: {'; '.join(suggested_fixes)}."
            tags = ['api', 'debugging']
            if app_name:
                tags.append(f'app.{app_name}')

        # Build complete bullet
        bullet = {
            'id': bullet_id,
            'title': title,
            'content': content,
            'tags': tags,
            'evidence': [{
                'type': 'execution',
                'ref': sample.get('id', 'unknown'),
                'note': f"Task failed with {error_type}: {error_analysis.get('root_cause', 'unknown error')}"
            }],
            'helpful_count': 0,
            'harmful_count': 0,
            'confidence': 'medium',
            'scope': 'app' if app_name else 'global',
            'prerequisites': [],
            'author': 'reflector',
            'status': 'active',
            'created': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'links': []
        }
        print(f"   ✅ RETURNING BULLET: id={bullet_id}, title={title[:40]}...")
        return bullet

    def _propose_new_bullets(
        self,
        sample: Dict,
        error_analysis: Dict,
        missing_guidance: List[str],
        success: bool
    ) -> List[Dict]:
        """
        Propose new bullets to fill gaps in playbook.

        Now enhanced to generate AppWorld-specific bullets from error_analysis.

        Returns:
            [{'id': 'bullet-...', 'title': '...', 'content': '...', ...}, ...]
        """
        new_bullets = []

        # DEBUG: Print entry state
        print(f"\n🔍 DEBUG _propose_new_bullets:")
        print(f"   success={success}")
        print(f"   error_analysis keys={list(error_analysis.keys())}")
        print(f"   error_type={error_analysis.get('error_type')}")
        print(f"   missing_patterns={error_analysis.get('missing_patterns')}")
        print(f"   error_messages={error_analysis.get('error_messages')}")

        # FIXED: Only skip bullet generation if task succeeded
        # For failures, ALWAYS try to generate bullets from error analysis
        if success:
            print(f"   ✅ Task succeeded, skipping bullet generation")
            return new_bullets  # Don't propose bullets for successful tasks

        # PRIORITY 1: Try to generate AppWorld-specific bullet from rich error analysis
        has_error_msgs = bool(error_analysis.get('error_messages'))
        has_missing_patterns = bool(error_analysis.get('missing_patterns'))
        print(f"   📊 Condition check: error_messages={has_error_msgs}, missing_patterns={has_missing_patterns}")

        if error_analysis.get('error_messages') or error_analysis.get('missing_patterns'):
            print(f"   ✅ Condition met, calling _generate_appworld_bullet()...")
            appworld_bullet = self._generate_appworld_bullet(sample, error_analysis)
            print(f"   📌 Returned bullet: {appworld_bullet is not None}")
            if appworld_bullet:
                print(f"   ✅ APPENDING BULLET: {appworld_bullet['id']}")
                new_bullets.append(appworld_bullet)
                return new_bullets  # One specific bullet is better than generic ones
            else:
                print(f"   ❌ _generate_appworld_bullet returned None!")
        else:
            print(f"   ❌ Condition NOT met, skipping AppWorld bullet generation")

        # FALLBACK: Generate generic bullets for backwards compatibility
        error_type = error_analysis.get('error_type')
        root_cause = error_analysis.get('root_cause')
        correct_approach = error_analysis.get('correct_approach')

        # Generate bullet ID
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        bullet_id = f"bullet-{timestamp}"

        # Propose bullet based on error type
        if error_type == 'incomplete_pagination':
            new_bullets.append({
                'id': bullet_id,
                'title': 'Implement pagination loops for API calls that return multiple pages',
                'content': (
                    'When fetching data from APIs that paginate results, always implement '
                    'a pagination loop using cursor or offset. Use while loop to fetch all '
                    'pages until no next_cursor is returned. Example: '
                    'cursor = None; while True: result = fetch(cursor); cursor = result.get("next_cursor"); if not cursor: break'
                ),
                'tags': ['pagination', 'api', 'loop', 'best_practice'],
                'evidence': [{
                    'type': 'execution',
                    'ref': sample.get('id', 'unknown'),
                    'note': f'Task failed due to: {root_cause}'
                }],
                'helpful_count': 0,
                'harmful_count': 0,
                'confidence': 'high',
                'scope': 'global',
                'prerequisites': [],
                'author': 'reflector',
                'status': 'active',
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'links': []
            })

        elif error_type == 'validation_missing':
            new_bullets.append({
                'id': bullet_id,
                'title': 'Validate inputs before processing in generated code',
                'content': (
                    'Always validate inputs before processing, especially for user-provided data. '
                    'Use assert statements or explicit checks for: non-empty strings, positive numbers, '
                    'valid formats. Validation prevents runtime errors and makes debugging easier.'
                ),
                'tags': ['validation', 'input_validation', 'error_prevention', 'best_practice'],
                'evidence': [{
                    'type': 'execution',
                    'ref': sample.get('id', 'unknown'),
                    'note': f'Task failed due to: {root_cause}'
                }],
                'helpful_count': 0,
                'harmful_count': 0,
                'confidence': 'high',
                'scope': 'global',
                'prerequisites': [],
                'author': 'reflector',
                'status': 'active',
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'links': []
            })

        elif error_type == 'bad_filters':
            new_bullets.append({
                'id': bullet_id,
                'title': 'Apply query filters based on task requirements',
                'content': (
                    'When task mentions specific filtering criteria (e.g., "only from Alice", '
                    '"messages after Monday"), apply those filters in the query or as post-processing. '
                    'Filter early in query when possible for efficiency. Use list comprehension for '
                    'post-filtering: [x for x in data if condition]'
                ),
                'tags': ['filter', 'query', 'data_processing', 'best_practice'],
                'evidence': [{
                    'type': 'execution',
                    'ref': sample.get('id', 'unknown'),
                    'note': f'Task failed due to: {root_cause}'
                }],
                'helpful_count': 0,
                'harmful_count': 0,
                'confidence': 'medium',
                'scope': 'global',
                'prerequisites': [],
                'author': 'reflector',
                'status': 'active',
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'links': []
            })

        return new_bullets

    def get_reflection_history(self) -> List[Dict]:
        """Return all reflections from this session."""
        return self.reflection_history.copy()

    def get_success_rate(self) -> float:
        """Calculate success rate from reflection history."""
        if not self.reflection_history:
            return 0.0

        successes = sum(1 for r in self.reflection_history if r['success'])
        return successes / len(self.reflection_history)
