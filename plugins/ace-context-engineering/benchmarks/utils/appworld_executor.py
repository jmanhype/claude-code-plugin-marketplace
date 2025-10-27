"""
AppWorld Executor for ACE Offline Adaptation

This executor integrates the interactive protocol with ACE's offline adaptation:
- Uses ClaudeCodeReActAgent to generate code via interactive protocol
- Executes code in AppWorld environment
- Captures rich execution feedback for bullet generation
- Returns detailed error analysis for reflector
"""

import sys
from pathlib import Path
from typing import Dict, List, Any

# Add AppWorld path
appworld_path = Path("/tmp/appworld/venv_appworld/lib/python3.11/site-packages")
if str(appworld_path) not in sys.path and appworld_path.exists():
    sys.path.insert(0, str(appworld_path))

try:
    from .claude_code_react_agent import ClaudeCodeReActAgent
    AGENT_AVAILABLE = True
    APPWORLD_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False
    APPWORLD_AVAILABLE = False


class AppWorldExecutor:
    """
    Executor that uses interactive protocol + AppWorld execution.

    Key differences from SkillsExecutor:
    1. Actually executes code in AppWorld (not simulated)
    2. Captures real API errors and test failures
    3. Provides rich feedback for bullet generation
    4. Uses multi-turn ReAct loop with execution feedback
    """

    def __init__(
        self,
        playbook_path: str,
        request_dir: str = "/tmp/appworld_requests",
        max_turns: int = 3,
        timeout_per_turn: int = 300,
        use_ace_generator: bool = True,
        use_faiss: bool = True
    ):
        """
        Args:
            playbook_path: Path to ACE playbook
            request_dir: Directory for request/response files
            max_turns: Max ReAct turns per task
            timeout_per_turn: Seconds to wait for response
            use_ace_generator: Use ACECodeGenerator (closes learning loop!)
            use_faiss: Use FAISS for semantic bullet retrieval
        """
        if not AGENT_AVAILABLE:
            raise ImportError("ClaudeCodeReActAgent not available")

        self.agent = ClaudeCodeReActAgent(
            playbook_path=playbook_path,
            request_dir=request_dir,
            max_turns=max_turns,
            timeout_per_turn=timeout_per_turn,
            use_ace_generator=use_ace_generator,
            use_faiss=use_faiss
        )

        self.execution_history = []

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
        Solve task using interactive protocol + AppWorld execution.

        Returns same format as SkillsExecutor for ACE compatibility,
        but with real execution results and rich error details.
        """
        # Build app descriptions from app list
        app_descriptions = {app: f"{app.capitalize()} API" for app in apps}

        # Solve using interactive agent
        result = self.agent.solve_task(
            instruction=instruction,
            apps=apps,
            app_descriptions=app_descriptions,
            task_id=task_id,
            ground_truth=ground_truth,
            playbook_bullets=playbook_bullets
        )

        # Extract rich execution feedback
        execution_history = result.get('execution_history', [])
        code_history = result.get('code_history', [])

        # Analyze failure patterns for reflector
        error_analysis = self._analyze_execution_errors(
            execution_history,
            code_history,
            instruction,
            apps
        )

        # Format for ACE compatibility
        return {
            'code': result['code'],
            'final_answer': result['final_answer'],
            'used_bullet_ids': result['used_bullet_ids'],
            'bullet_feedback': result['bullet_feedback'],
            'success': result['success'],
            'strategies_applied': [],  # Not used with real execution
            'execution_feedback': {
                'tgc': result.get('tgc', 0.0),
                'sgc': result.get('sgc', 0.0),
                'turns_used': result.get('turns', 0),
                'execution_history': execution_history,
                'code_history': code_history,
                'error_analysis': error_analysis
            }
        }

    def _analyze_execution_errors(
        self,
        execution_history: List[Dict],
        code_history: List[str],
        instruction: str,
        apps: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze execution history to extract actionable failure patterns.

        This is the KEY method that enables bullet generation:
        - Identifies API errors
        - Detects missing authentication
        - Finds pagination issues
        - Extracts error messages

        Returns structured error analysis for reflector.
        """
        analysis = {
            'error_type': None,
            'error_messages': [],
            'failed_apis': [],
            'missing_patterns': [],
            'suggested_fixes': []
        }

        if not execution_history:
            return analysis

        # Check final result
        final_result = execution_history[-1]
        if final_result.get('success'):
            analysis['error_type'] = None
            return analysis

        # Analyze error messages
        print(f"\n🔍 DEBUG AppWorldExecutor._analyze_execution_errors:")
        print(f"   execution_history length: {len(execution_history)}")

        for turn_idx, turn_result in enumerate(execution_history):
            result_msg = turn_result.get('result', '')
            tgc = turn_result.get('tgc', 0.0)
            print(f"   Turn {turn_idx}: tgc={tgc}, has 'Execution error': {'Execution error:' in result_msg}")

            # Execution errors
            if 'Execution error:' in result_msg:
                analysis['error_messages'].append(result_msg)
                print(f"      → Added execution error message")

                # Check for specific patterns
                if 'AttributeError' in result_msg or 'KeyError' in result_msg:
                    analysis['error_type'] = 'api_misuse'
                    analysis['missing_patterns'].append('Need correct API method names')
                    print(f"      → Set error_type=api_misuse")

                elif 'access_token' in result_msg or 'authentication' in result_msg.lower():
                    analysis['error_type'] = 'authentication_error'
                    analysis['missing_patterns'].append('Always call login() first')
                    print(f"      → Set error_type=authentication_error")

                elif 'NoneType' in result_msg:
                    analysis['error_type'] = 'missing_data'
                    analysis['missing_patterns'].append('Check API response structure')
                    print(f"      → Set error_type=missing_data")

            # Test failures (TGC < 1.0)
            elif turn_result.get('tgc', 0.0) < 1.0:
                print(f"      → TGC < 1.0, processing test failure")
                num_tests = turn_result.get('result', '').split('/')
                if len(num_tests) == 2:
                    passed, total = num_tests[0].split('(')[-1], num_tests[1].split(' ')[0]
                    analysis['error_messages'].append(
                        f"Tests failed: {passed}/{total}"
                    )
                    print(f"      → Added test failure message: {passed}/{total}")

                # If no execution errors but tests failed, it's logic error
                if analysis['error_type'] is None:
                    analysis['error_type'] = 'logic_error'
                    analysis['missing_patterns'].append('Check task logic and requirements')
                    print(f"      → Set error_type=logic_error, added missing_pattern")
                else:
                    print(f"      → error_type already set to {analysis['error_type']}, skipping logic_error")

        print(f"   Final error_analysis:")
        print(f"      error_type: {analysis['error_type']}")
        print(f"      error_messages: {analysis['error_messages']}")
        print(f"      missing_patterns: {analysis['missing_patterns']}")

        # Analyze code patterns
        if code_history:
            final_code = code_history[-1]

            # Check for common issues
            for app in apps:
                # Missing login?
                if f"{app}.login()" not in final_code:
                    analysis['missing_patterns'].append(
                        f"Missing login() call for {app}"
                    )
                    analysis['failed_apis'].append(f"{app}.login")

                # Using generic methods?
                if f"{app}.get_" in final_code or f"{app}.fetch_" in final_code:
                    analysis['suggested_fixes'].append(
                        f"Use search_* methods for {app}, not get_/fetch_"
                    )

        # Default to wrong_source if we can't identify specific error
        if analysis['error_type'] is None and not final_result.get('success'):
            analysis['error_type'] = 'wrong_source'
            analysis['missing_patterns'].append('May be querying wrong data source')

        return analysis


def create_appworld_executor(
    playbook_path: str,
    use_ace_generator: bool = True,
    **kwargs
) -> AppWorldExecutor:
    """
    Factory function to create AppWorldExecutor with ACECodeGenerator.

    Args:
        playbook_path: Path to ACE playbook
        use_ace_generator: Use ACECodeGenerator (default: True, closes learning loop!)
        **kwargs: Additional parameters for AppWorldExecutor

    Usage in run_offline_adaptation.py:
    ```python
    from utils.appworld_executor import create_appworld_executor

    executor = create_appworld_executor(
        playbook_path=str(playbook_path),
        use_ace_generator=True  # CLOSES THE LEARNING LOOP!
    )
    ace = ClaudeCodeACE(
        playbook_path=str(playbook_path),
        executor=executor,
        use_faiss=USE_FAISS
    )
    ```
    """
    return AppWorldExecutor(
        playbook_path,
        use_ace_generator=use_ace_generator,
        **kwargs
    )
