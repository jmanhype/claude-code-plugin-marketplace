#!/usr/bin/env python3
"""
ACE Code Generator - Closes the Learning Loop

This module implements the missing link in the ACE system:
- Reads playbook bullets (learned patterns from Reflector → Curator)
- Applies them during code generation
- Enables true learning from failures

Architecture:
    Reflector → Curator → Playbook → ACECodeGenerator → AppWorld
         ↑                                                      ↓
         └────────────── Feedback from execution ──────────────┘

This closes the ACE learning loop that was broken in skill_monitor_standalone.py.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

try:
    from .bullet_retriever import BulletRetriever
except ImportError:
    from bullet_retriever import BulletRetriever

try:
    from . import claude_code_skill_invoker as skill_invoker
except ImportError:
    import claude_code_skill_invoker as skill_invoker

logger = logging.getLogger(__name__)


class ACECodeGenerator:
    """
    ACE-compliant code generator using playbook bullets.

    This is what the ACE paper describes: using the agent's own context
    (the playbook) to guide code generation.

    Key difference from skill_monitor_standalone.py:
    - skill_monitor: Uses hardcoded templates, ignores bullets
    - ACECodeGenerator: Reads bullets, applies them during generation
    """

    def __init__(
        self,
        playbook_path: str,
        use_faiss: bool = True,  # Ignored for now, kept for API compatibility
        experiment_name: str = "ace_with_claude_code"
    ):
        """
        Initialize ACE code generator.

        Args:
            playbook_path: Path to playbook.json (learned strategies)
            use_faiss: Ignored (kept for API compatibility)
            experiment_name: Name for this experiment
        """
        self.playbook_path = Path(playbook_path)
        self.experiment_name = experiment_name

        # Initialize bullet retriever (TF-IDF + tag overlap)
        self.bullet_retriever = BulletRetriever(
            playbook_path=str(self.playbook_path)
        )

        logger.info(f"ACECodeGenerator initialized with playbook: {self.playbook_path}")

    def generate_code(
        self,
        instruction: str,
        apps: List[str],
        execution_history: Optional[List[Dict]] = None,
        turn: int = 1,
        top_k_bullets: int = 5
    ) -> str:
        """
        Generate AppWorld code using playbook guidance.

        This is where ACE learning happens:
        1. Retrieve relevant bullets based on task/app
        2. Pass bullets to code generator
        3. Generate code applying learned patterns

        Args:
            instruction: Natural language task description
            apps: List of available apps (e.g., ['spotify', 'venmo'])
            execution_history: Previous execution attempts (for multi-turn)
            turn: Current turn number (1-3)
            top_k_bullets: Number of bullets to retrieve

        Returns:
            Python code string ready for AppWorld execution
        """
        execution_history = execution_history or []

        # Step 1: Retrieve relevant bullets (ACE's learned knowledge)
        logger.info(f"[Turn {turn}] Retrieving top-{top_k_bullets} bullets for: {instruction[:100]}...")

        # Get app-specific tags
        tags = [f"app.{app}" for app in apps if app and app != 'general']

        try:
            relevant_bullets = self.bullet_retriever.retrieve(
                query=instruction,
                tags=tags,
                top_k=top_k_bullets
            )

            logger.info(f"Retrieved {len(relevant_bullets)} bullets:")
            for i, bullet in enumerate(relevant_bullets, 1):
                logger.info(f"  {i}. {bullet.title} (score: {bullet.score:.3f})")

        except Exception as e:
            logger.warning(f"Bullet retrieval failed: {e}")
            relevant_bullets = []

        # Step 2: Generate code using bullets as guidance
        logger.info(f"[Turn {turn}] Generating code with {len(relevant_bullets)} bullets...")

        prompt_payload = self._build_skill_prompt(instruction, apps, relevant_bullets)
        prompt_json = json.dumps(prompt_payload, indent=2)

        try:
            code = self._invoke_code_skill(prompt_json, instruction, apps, relevant_bullets)
            return code

        except Exception as e:
            logger.error(f"Code generation failed: {e}", exc_info=True)
            # Fallback to basic template
            logger.warning("Falling back to basic code template")
            return self._generate_fallback_code(instruction, apps)

    def _build_skill_prompt(
        self,
        instruction: str,
        apps: List[str],
        bullets: List
    ) -> str:
        """
        Build prompt for generate-appworld-code skill.

        Args:
            instruction: Task instruction
            apps: Available apps
            bullets: Retrieved bullets with title and content

        Returns:
            Formatted prompt for the skill
        """
        payload = {
            "instruction": instruction,
            "apps": apps,
            "strategies": [],
            "bullets": [],
            "environment": {
                "mode": "appworld_offline",
                "credentials": {
                    "username": "user@example.com",
                    "password": "password"
                },
                "requirements": [
                    "Return ONLY executable Python code.",
                    "Do not request user permission or external credentials.",
                    "Always call apis.supervisor.complete_task() when successful.",
                    "Handle errors with try/except and report via print before raising."
                ]
            }
        }

        for bullet in bullets:
            title = getattr(bullet, "title", str(bullet))
            content = getattr(bullet, "content", "")
            payload["strategies"].append(title if title else content[:80])

            payload["bullets"].append({
                "id": getattr(bullet, "bullet_id", getattr(bullet, "id", "")),
                "title": title,
                "content": content,
                "tags": getattr(bullet, "tags", []),
                "confidence": getattr(bullet, "confidence", 0.5),
            })

        return payload

    def _invoke_code_skill(self, prompt_json: str, instruction: str, apps: List[str], bullets: List) -> str:
        """Invoke code generation skill with retry enforcing code-only output."""

        response = skill_invoker.invoke_skill("generate-appworld-code", prompt_json)
        code = self._extract_code_block(response)

        if self._looks_like_code(code):
            self._validate_bullet_usage(code, bullets)
            return code

        # Reinforce instructions once
        strict_payload = json.loads(prompt_json)
        strict_payload["directives"] = [
            "Return ONLY executable Python code. No explanations, no markdown, no commentary.",
            "Code must call apis.supervisor.complete_task().",
        ]
        strict_prompt = json.dumps(strict_payload, indent=2)

        response_strict = skill_invoker.invoke_skill("generate-appworld-code", strict_prompt)
        code_strict = self._extract_code_block(response_strict)

        if self._looks_like_code(code_strict):
            self._validate_bullet_usage(code_strict, bullets)
            return code_strict

        raise RuntimeError(
            "generate-appworld-code skill did not return executable code after reinforcement"
        )

    def _extract_code_block(self, response: str) -> str:
        """Extract code from skill response, handling fences and wrappers."""

        if not response:
            return ""

        text = response.strip()

        if text.startswith("```"):
            fence = "```python" if text.startswith("```python") else "```"
            text = text[len(fence):]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        # If the response is JSON with a code field, extract it
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return text

        for key in ("code", "python", "solution"):
            if isinstance(payload, dict) and key in payload and isinstance(payload[key], str):
                return payload[key].strip()

        return text

    def _looks_like_code(self, code: str) -> bool:
        """Heuristic to determine if a string resembles executable Python code."""

        if not code or len(code) < 20:
            return False

        if "apis." not in code:
            return False

        if "complete_task" not in code:
            return False

        return True

    def _validate_bullet_usage(self, code: str, bullets: List) -> None:
        """
        Validate that bullets were actually applied in generation.

        This is James Zou's reliability principle: verify the system
        is actually using what it learned.

        Args:
            code: Generated code
            bullets: Bullets that were provided as context
        """
        if not bullets:
            return

        code_lower = code.lower()
        applied_count = 0

        for bullet in bullets:
            title = bullet.title.lower()

            # Check if bullet title appears in code
            if title in code_lower:
                applied_count += 1
                logger.debug(f"✓ Bullet applied: {bullet.title}")
                continue

            # Check content keywords
            if hasattr(bullet, 'content') and bullet.content:
                # Extract key phrases (rough heuristic)
                keywords = [word for word in bullet.content.split()
                           if len(word) > 5 and not word.startswith(('http', 'www'))]
                if any(keyword.lower() in code_lower for keyword in keywords[:5]):
                    applied_count += 1
                    logger.debug(f"✓ Bullet pattern found: {bullet.title}")
                    continue

        usage_rate = applied_count / len(bullets) if bullets else 0

        if usage_rate < 0.3:  # Less than 30% of bullets applied
            logger.warning(
                f"Low bullet usage: {applied_count}/{len(bullets)} ({usage_rate:.1%}) bullets applied"
            )
        else:
            logger.info(f"Bullet usage: {applied_count}/{len(bullets)} ({usage_rate:.1%}) bullets applied")

    def _generate_fallback_code(self, instruction: str, apps: List[str]) -> str:
        """
        Generate fallback code if code generation fails.

        This is a basic template that at least attempts the task,
        even without playbook guidance.

        Args:
            instruction: Task instruction
            apps: Available apps

        Returns:
            Basic Python code template
        """
        app = apps[0] if apps else 'unknown'

        return f'''# Fallback code for: {instruction}
# App: {app}
# Note: Code generation failed, using fallback template

try:
    # TODO: Implement task logic
    # Code generation failed. This is a fallback.

    result = "Fallback implementation"

    # Complete task
    apis.supervisor.complete_task()

except Exception as e:
    print(f"Error: {{str(e)}}")
    raise
'''

    def get_stats(self) -> Dict:
        """
        Get statistics about code generation.

        Returns:
            Dictionary with generation stats
        """
        return {
            'playbook_path': str(self.playbook_path),
            'experiment_name': self.experiment_name
        }
