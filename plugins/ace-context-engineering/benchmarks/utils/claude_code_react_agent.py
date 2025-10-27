"""
Claude Code ReAct Agent for AppWorld with ACE Integration

This adapter wraps the official AppWorld ReAct agent and uses
ACECodeGenerator for code generation, which applies ACE playbook
bullets as guidance via Claude Code skill invocation.

This CLOSES THE ACE LEARNING LOOP by making the generator actually
use the playbook bullets during code generation.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Try to import AppWorld for execution
try:
    appworld_path = Path("/tmp/appworld/venv_appworld/lib/python3.11/site-packages")
    if str(appworld_path) not in sys.path and appworld_path.exists():
        sys.path.insert(0, str(appworld_path))
    from appworld import AppWorld
    APPWORLD_AVAILABLE = True
except ImportError:
    APPWORLD_AVAILABLE = False

# Import ACE Code Generator (closes learning loop)
try:
    from .ace_code_generator import ACECodeGenerator
    ACE_GENERATOR_AVAILABLE = True
except ImportError:
    try:
        from ace_code_generator import ACECodeGenerator
        ACE_GENERATOR_AVAILABLE = True
    except ImportError:
        ACE_GENERATOR_AVAILABLE = False


class ClaudeCodeReActAgent:
    """
    Interactive ReAct agent that asks Claude Code to generate code.

    Workflow:
    1. Receive task instruction + app descriptions from AppWorld
    2. Retrieve relevant bullets from ACE playbook
    3. Write code generation request to file
    4. Wait for Claude Code to generate code (via Skill)
    5. Read generated code from response file
    6. Return code to AppWorld for execution
    7. Receive execution feedback
    8. Repeat with updated context
    """

    def __init__(
        self,
        playbook_path: str,
        request_dir: str = "/tmp/appworld_requests",
        max_turns: int = 10,
        timeout_per_turn: int = 300,  # 5 minutes
        experiment_name: str = "ace_interactive",
        use_ace_generator: bool = True,
        use_faiss: bool = True
    ):
        """
        Args:
            playbook_path: Path to ACE playbook.json
            request_dir: Directory for request/response files (fallback only)
            max_turns: Maximum ReAct turns per task
            timeout_per_turn: Seconds to wait for Claude Code response
            experiment_name: AppWorld experiment name
            use_ace_generator: Use ACECodeGenerator (closes learning loop)
            use_faiss: Use FAISS for semantic bullet retrieval
        """
        self.playbook_path = playbook_path
        self.request_dir = Path(request_dir)
        self.request_dir.mkdir(parents=True, exist_ok=True)
        self.max_turns = max_turns
        self.timeout_per_turn = timeout_per_turn
        self.experiment_name = experiment_name
        self.use_ace_generator = use_ace_generator and ACE_GENERATOR_AVAILABLE

        # Load playbook
        with open(playbook_path, 'r') as f:
            self.playbook = json.load(f)

        # Initialize ACE Code Generator (closes learning loop!)
        if self.use_ace_generator:
            try:
                self.code_generator = ACECodeGenerator(
                    playbook_path=playbook_path,
                    use_faiss=use_faiss,
                    experiment_name=experiment_name
                )
                print(f"✅ ACE Code Generator initialized (LEARNING LOOP CLOSED)")
            except Exception as e:
                print(f"⚠️  Failed to initialize ACE Code Generator: {e}")
                print(f"   Falling back to interactive protocol")
                self.use_ace_generator = False
                self.code_generator = None
        else:
            self.code_generator = None
            print(f"⚠️  Using legacy interactive protocol (learning loop OPEN)")

        print(f"✓ ClaudeCodeReActAgent initialized")
        print(f"  Playbook: {playbook_path}")
        print(f"  Bullets: {len(self.playbook.get('bullets', []))}")
        print(f"  ACE Generator: {'✓' if self.use_ace_generator else '✗'}")
        print(f"  Request dir: {request_dir}")
        print(f"  AppWorld execution: {'✓' if APPWORLD_AVAILABLE else '✗'}")

    def retrieve_bullets(
        self,
        instruction: str,
        apps: List[str]
    ) -> List[Dict]:
        """
        Retrieve relevant bullets from playbook for task.

        Simple tag-based retrieval:
        - Match app names
        - Match keywords in instruction
        """
        bullets = self.playbook.get('bullets', [])
        relevant = []

        instruction_lower = instruction.lower()

        for bullet in bullets:
            if bullet.get('status') != 'active':
                continue

            tags = bullet.get('tags', [])
            score = 0

            # App matching
            for app in apps:
                if app.lower() in ' '.join(tags).lower():
                    score += 2

            # Keyword matching
            keywords = ['login', 'auth', 'api', 'error', 'validate']
            for kw in keywords:
                if kw in instruction_lower and kw in ' '.join(tags).lower():
                    score += 1

            if score > 0:
                relevant.append((score, bullet))

        # Sort by score and take top 5
        relevant.sort(reverse=True, key=lambda x: x[0])
        return [b for (score, b) in relevant[:5]]

    def generate_code(
        self,
        instruction: str,
        apps: List[str],
        execution_history: List[Dict],
        turn: int
    ) -> str:
        """
        Generate code using ACE Code Generator (closes learning loop).

        This method uses the ACECodeGenerator which:
        1. Retrieves relevant bullets from playbook
        2. Invokes Claude Code skill with bullet context
        3. Returns code that applies learned patterns

        Args:
            instruction: Task instruction
            apps: Available apps
            execution_history: Previous execution attempts
            turn: Current turn number

        Returns:
            Generated code ready for AppWorld execution
        """
        print(f"\n🔍 DEBUG generate_code called:")
        print(f"   use_ace_generator: {self.use_ace_generator}")
        print(f"   code_generator exists: {self.code_generator is not None}")
        print(f"   code_generator type: {type(self.code_generator).__name__ if self.code_generator else 'None'}")

        if self.use_ace_generator and self.code_generator:
            try:
                print(f"✓ Calling ACECodeGenerator.generate_code()...")
                code = self.code_generator.generate_code(
                    instruction=instruction,
                    apps=apps,
                    execution_history=execution_history,
                    turn=turn
                )
                print(f"✓ ACE Code Generator succeeded! Generated {len(code.splitlines())} lines")
                return code
            except Exception as e:
                print(f"⚠️  ACE Code Generator failed: {e}")
                import traceback
                traceback.print_exc()
                print(f"   Falling back to interactive protocol")
                # Fall through to interactive protocol

        # Fallback to interactive protocol if ACE generator unavailable
        print(f"⚠️  Using interactive protocol (ACE not available)")
        return self.generate_code_interactive(
            instruction=instruction,
            apps=apps,
            app_descriptions={},  # Not needed for interactive protocol
            bullets=self.retrieve_bullets(instruction, apps),
            execution_history=execution_history,
            turn=turn
        )

    def generate_code_interactive(
        self,
        instruction: str,
        apps: List[str],
        app_descriptions: Dict[str, str],
        bullets: List[Dict],
        execution_history: List[Dict],
        turn: int
    ) -> str:
        """
        Request code generation from Claude Code via interactive protocol.

        LEGACY METHOD: This is the old file-based protocol that doesn't
        actually use bullets during code generation (broken learning loop).

        Kept for backward compatibility and as fallback.

        Protocol:
        1. Write request.json with all context
        2. Wait for response.json (or timeout)
        3. Read generated code from response
        4. Clean up files
        """
        # Build request
        request = {
            "turn": turn,
            "instruction": instruction,
            "apps": apps,
            "app_descriptions": app_descriptions,
            "bullets": [
                {
                    "id": b.get('id'),
                    "title": b.get('title'),
                    "content": b.get('content'),
                    "tags": b.get('tags', [])
                }
                for b in bullets
            ],
            "execution_history": execution_history,
            "timestamp": time.time()
        }

        # Write request
        request_file = self.request_dir / f"request_turn_{turn}.json"
        response_file = self.request_dir / f"response_turn_{turn}.json"

        # Clean old response
        if response_file.exists():
            response_file.unlink()

        with open(request_file, 'w') as f:
            json.dump(request, f, indent=2)

        print(f"\n{'='*70}")
        print(f"🤖 CODE GENERATION REQUEST (Turn {turn}/{self.max_turns})")
        print(f"{'='*70}")
        print(f"Task: {instruction[:80]}...")
        print(f"Apps: {', '.join(apps)}")
        print(f"Bullets: {len(bullets)} guidance points")
        print(f"History: {len(execution_history)} previous turns")
        print(f"\n📝 Request saved to: {request_file}")
        print(f"⏳ Waiting for Claude Code to generate code...")
        print(f"   (Expected response file: {response_file})")
        print(f"   (Timeout: {self.timeout_per_turn}s)")
        print(f"\n⚠️  CLAUDE CODE: Please read the request and generate code!")
        print(f"   Use the 'generate-appworld-code' Skill")
        print(f"   Write response to: {response_file}")
        print(f"{'='*70}\n")

        # Wait for response
        start_time = time.time()
        while time.time() - start_time < self.timeout_per_turn:
            if response_file.exists():
                # Response received!
                try:
                    with open(response_file, 'r') as f:
                        response = json.load(f)

                    code = response.get('code', '')
                    reasoning = response.get('reasoning', '')

                    print(f"\n✅ Code received from Claude Code!")
                    if reasoning:
                        print(f"   Reasoning: {reasoning[:100]}...")
                    print(f"   Code length: {len(code)} characters\n")

                    # Clean up
                    request_file.unlink()
                    response_file.unlink()

                    return code

                except Exception as e:
                    print(f"⚠️  Error reading response: {e}")
                    time.sleep(1)
                    continue

            # Poll every second
            time.sleep(1)

            # Print progress
            elapsed = int(time.time() - start_time)
            if elapsed % 30 == 0:  # Every 30 seconds
                print(f"   Still waiting... ({elapsed}s / {self.timeout_per_turn}s)")

        # Timeout
        print(f"\n❌ TIMEOUT: No response received after {self.timeout_per_turn}s")
        print(f"   Falling back to generic code\n")

        return self._generate_fallback_code(instruction, apps)

    def _generate_fallback_code(self, instruction: str, apps: List[str]) -> str:
        """Generate basic fallback code if Claude Code doesn't respond."""
        return f"""# Fallback code (Claude Code did not respond)
# Task: {instruction}

print("⚠️  Fallback code - Claude Code integration needed")
print("Task: {instruction[:50]}...")

# Complete task (will likely fail)
apis.supervisor.complete_task()
"""

    def _execute_in_appworld(
        self,
        task_id: str,
        code: str
    ) -> Tuple[str, bool, float, float]:
        """
        Execute code in AppWorld environment and evaluate.

        Returns:
            (result_message, success, tgc, sgc)
        """
        if not APPWORLD_AVAILABLE:
            return "AppWorld not available", False, 0.0, 0.0

        try:
            # Load task
            with AppWorld(task_id=task_id, experiment_name=self.experiment_name) as world:
                # Execute code
                try:
                    world.execute(code)
                    executed = True
                except Exception as exec_error:
                    result_message = f"Execution error: {str(exec_error)}"
                    return result_message, False, 0.0, 0.0

                # Evaluate
                try:
                    test_tracker = world.evaluate()

                    # Get test results
                    success = test_tracker.success  # True if all tests passed
                    pass_percentage = test_tracker.pass_percentage  # Percentage of tests passed

                    # Convert to TGC/SGC format
                    # TGC = pass_percentage / 100 (0.0 to 1.0)
                    # SGC = same as TGC for single task
                    tgc = pass_percentage / 100.0
                    sgc = tgc

                    result_message = f"TGC: {tgc:.2f}, SGC: {sgc:.2f} ({test_tracker.pass_count}/{test_tracker.num_tests} tests passed)"

                    return result_message, success, tgc, sgc

                except Exception as eval_error:
                    result_message = f"Evaluation error: {str(eval_error)}"
                    return result_message, False, 0.0, 0.0

        except Exception as e:
            result_message = f"AppWorld error: {str(e)}"
            return result_message, False, 0.0, 0.0

    def solve_task(
        self,
        instruction: str,
        apps: List[str],
        app_descriptions: Dict[str, str],
        task_id: str,
        ground_truth: str = None,
        apis: List[Dict] = None,
        playbook_bullets: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Solve AppWorld task using interactive ReAct loop with execution.

        ReAct Loop:
        1. Retrieve bullets
        2. Generate code (ask Claude Code)
        3. Execute code in AppWorld
        4. Receive feedback (TGC/SGC)
        5. If failed and turns remaining, repeat with feedback

        Returns:
            {
                'code': final code,
                'final_answer': execution result message,
                'used_bullet_ids': [...],
                'bullet_feedback': {'bullet-id': 'helpful'|'harmful'},
                'success': bool,
                'tgc': Task Goal Completion,
                'sgc': Scenario Goal Completion,
                'code_history': [code1, code2, ...],
                'execution_history': [result1, result2, ...],
                'turns': number_of_turns
            }
        """
        print(f"\n{'#'*70}")
        print(f"SOLVING TASK: {task_id}")
        print(f"{'#'*70}")
        print(f"Instruction: {instruction}")
        print(f"Apps: {', '.join(apps)}")
        print(f"{'#'*70}\n")

        # Retrieve bullets (use provided bullets or retrieve from playbook)
        if playbook_bullets:
            bullets = playbook_bullets
        else:
            bullets = self.retrieve_bullets(instruction, apps)

        code_history = []
        execution_history = []
        final_tgc = 0.0
        final_sgc = 0.0
        final_success = False
        final_result = ""

        for turn in range(1, self.max_turns + 1):
            # Generate code using ACE Code Generator (closes learning loop!)
            code = self.generate_code(
                instruction=instruction,
                apps=apps,
                execution_history=execution_history,
                turn=turn
            )

            code_history.append(code)

            # Execute code in AppWorld
            print(f"\n{'='*70}")
            print(f"🚀 EXECUTING CODE IN APPWORLD")
            print(f"{'='*70}\n")

            result_message, success, tgc, sgc = self._execute_in_appworld(
                task_id, code
            )

            print(f"\n📊 EXECUTION RESULT:")
            print(f"  {result_message}")
            print(f"  Success: {'✅' if success else '❌'}")
            print(f"  TGC: {tgc:.2f}")
            print(f"  SGC: {sgc:.2f}\n")

            execution_history.append({
                'turn': turn,
                'result': result_message,
                'success': success,
                'tgc': tgc,
                'sgc': sgc
            })

            final_tgc = tgc
            final_sgc = sgc
            final_success = success
            final_result = result_message

            # If succeeded or max turns reached, stop
            if success or turn >= self.max_turns:
                break

            # Otherwise, continue with feedback for next turn

        # Evaluate bullet effectiveness based on TGC (partial success counts!)
        bullet_feedback = {}
        for bullet in bullets:
            bullet_id = bullet['id']
            # If task achieved ANY success (TGC > 0), bullets were helpful
            # Only mark as harmful if TGC == 0 (complete failure)
            # This allows learning from partial successes
            bullet_feedback[bullet_id] = 'helpful' if final_tgc > 0 else 'harmful'

        return {
            'code': code_history[-1] if code_history else '',
            'final_answer': final_result,
            'used_bullet_ids': [b['id'] for b in bullets],
            'bullet_feedback': bullet_feedback,
            'success': final_success,
            'tgc': final_tgc,
            'sgc': final_sgc,
            'code_history': code_history,
            'execution_history': execution_history,
            'turns': len(code_history),
            'bullets_used': bullets  # For compatibility
        }


def create_response_file(response_path: str, code: str, reasoning: str = ""):
    """
    Helper for Claude Code to create response file.

    Usage from Claude Code:
    ```python
    from benchmarks.utils.claude_code_react_agent import create_response_file
    create_response_file(
        "/tmp/appworld_requests/response_turn_1.json",
        code="# Generated code here",
        reasoning="I used the Spotify API pattern from the playbook"
    )
    ```
    """
    response = {
        "code": code,
        "reasoning": reasoning,
        "timestamp": time.time()
    }

    with open(response_path, 'w') as f:
        json.dump(response, f, indent=2)

    print(f"✅ Response written to: {response_path}")
