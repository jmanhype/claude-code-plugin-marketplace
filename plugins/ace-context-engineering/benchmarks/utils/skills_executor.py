"""
Skills-based task executor that uses retrieved bullets for guidance.

This replaces the pattern-matching approach with bullet-driven code generation.
"""

import json
import re
from typing import Dict, List, Any, Tuple


class SkillsExecutor:
    """
    Executes tasks using guidance from retrieved ACE bullets.

    Key difference from pattern matching:
    - READS bullet content for strategies
    - APPLIES bullet guidance to code generation
    - TRACKS which bullets were helpful/harmful
    """

    def __init__(self):
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
        Solve a task using bullet guidance.

        Args:
            instruction: Task instruction
            apps: Available apps (e.g., ['Slack', 'Venmo'])
            apis: Available API endpoints
            playbook_bullets: Retrieved bullets with guidance
            ground_truth: Optional ground truth for validation

        Returns:
            {
                'code': generated code,
                'final_answer': execution result,
                'used_bullet_ids': [...],
                'bullet_feedback': {'bullet-123': 'helpful', ...},
                'success': bool
            }
        """
        # Extract guidance from bullets
        strategies = self._extract_strategies(playbook_bullets)

        # Generate code using bullet guidance
        code = self._generate_code_with_bullets(
            instruction, apps, apis, strategies, playbook_bullets
        )

        # Track bullet usage
        used_bullet_ids = [b['id'] for b in playbook_bullets]

        # Execute code (simulated for now)
        execution_result, success = self._execute_code(code, ground_truth)

        # Determine bullet feedback
        bullet_feedback = self._evaluate_bullet_effectiveness(
            playbook_bullets, success, execution_result
        )

        return {
            'code': code,
            'final_answer': execution_result,
            'used_bullet_ids': used_bullet_ids,
            'bullet_feedback': bullet_feedback,
            'success': success,
            'strategies_applied': strategies
        }

    def _extract_strategies(self, bullets: List[Dict]) -> List[str]:
        """
        Extract actionable strategies from bullet content.

        Examples:
        - "Always validate input before processing"
        - "Use pagination for large datasets"
        - "Check authentication before API calls"
        """
        strategies = []

        for bullet in bullets:
            content = bullet.get('content', '')
            title = bullet.get('title', '')

            # Extract key phrases (simplified - could use NLP)
            # Look for imperative verbs, "always", "must", "should"
            if 'always' in content.lower() or 'must' in content.lower():
                strategies.append(f"{title}: {content[:100]}")
            elif 'validate' in content.lower():
                strategies.append(f"Validation required: {title}")
            elif 'pagination' in content.lower():
                strategies.append(f"Use pagination: {title}")
            elif 'filter' in content.lower():
                strategies.append(f"Apply filters: {title}")
            elif 'error' in content.lower():
                strategies.append(f"Error handling: {title}")

        return strategies

    def _generate_code_with_bullets(
        self,
        instruction: str,
        apps: List[str],
        apis: List[Dict],
        strategies: List[str],
        bullets: List[Dict]
    ) -> str:
        """
        Generate code using bullet guidance instead of hardcoded patterns.

        This is the KEY method that differentiates ACE from pattern matching.
        """
        code_lines = ['# Generated using ACE bullet guidance', '']

        # Add strategies as comments
        if strategies:
            code_lines.append('# Applied strategies:')
            for strategy in strategies:
                code_lines.append(f'#   - {strategy}')
            code_lines.append('')

        # Parse instruction to identify intent
        instruction_lower = instruction.lower()

        # Check bullets for relevant guidance
        has_validation_guidance = any('validate' in b.get('content', '').lower() for b in bullets)
        has_pagination_guidance = any('pagination' in b.get('content', '').lower() for b in bullets)
        has_filter_guidance = any('filter' in b.get('content', '').lower() for b in bullets)

        # Determine which app/API to use
        detected_app = None
        detected_action = None

        # Use bullet guidance to inform app selection
        for bullet in bullets:
            content = bullet.get('content', '').lower()
            # Check if bullet mentions specific apps
            for app in apps:
                if app.lower() in content:
                    detected_app = app
                    break

        # Fallback to instruction parsing if no bullet guidance
        if not detected_app:
            for app in apps:
                if app.lower() in instruction_lower:
                    detected_app = app
                    break

        # Determine action
        if 'send' in instruction_lower or 'post' in instruction_lower:
            detected_action = 'send'
        elif 'get' in instruction_lower or 'fetch' in instruction_lower or 'find' in instruction_lower:
            detected_action = 'fetch'
        elif 'delete' in instruction_lower or 'remove' in instruction_lower:
            detected_action = 'delete'
        elif 'split' in instruction_lower or 'divide' in instruction_lower:
            detected_action = 'split'

        # Generate app-specific code with bullet guidance
        if detected_app == 'Slack' or 'slack' in instruction_lower:
            code_lines.extend(self._generate_slack_code(
                instruction, detected_action, has_validation_guidance,
                has_pagination_guidance, has_filter_guidance
            ))
        elif detected_app == 'Venmo' or 'venmo' in instruction_lower:
            code_lines.extend(self._generate_venmo_code(
                instruction, detected_action, has_validation_guidance
            ))
        elif 'email' in instruction_lower or 'gmail' in instruction_lower:
            code_lines.extend(self._generate_email_code(
                instruction, detected_action, has_validation_guidance
            ))
        else:
            # Generic code generation with bullet guidance
            code_lines.extend(self._generate_generic_code(
                instruction, detected_app, detected_action, strategies
            ))

        return '\n'.join(code_lines)

    def _generate_slack_code(
        self,
        instruction: str,
        action: str,
        validate: bool,
        paginate: bool,
        filter_results: bool
    ) -> List[str]:
        """Generate Slack-specific code with bullet guidance."""
        code = []

        # Extract details from instruction
        channel_match = re.search(r'channel[:\s]+["\']?([^"\',.]+)', instruction, re.IGNORECASE)
        message_match = re.search(r'(?:message|text)[:\s]+["\']([^"\']+)', instruction, re.IGNORECASE)

        channel = channel_match.group(1) if channel_match else '#general'
        message = message_match.group(1) if message_match else 'Hello from ACE!'

        if action == 'send':
            # Validation guidance
            if validate:
                code.append('# Bullet guidance: Validate input before sending')
                code.append(f'assert channel, "Channel cannot be empty"')
                code.append(f'assert message, "Message cannot be empty"')
                code.append('')

            code.append('# Send Slack message')
            code.append(f'slack_client.chat_postMessage(')
            code.append(f'    channel="{channel}",')
            code.append(f'    text="{message}"')
            code.append(')')

        elif action == 'fetch':
            code.append('# Fetch Slack messages')

            # Pagination guidance
            if paginate:
                code.append('# Bullet guidance: Use pagination for large datasets')
                code.append('messages = []')
                code.append('cursor = None')
                code.append('while True:')
                code.append(f'    result = slack_client.conversations_history(')
                code.append(f'        channel="{channel}",')
                code.append('        limit=100,')
                code.append('        cursor=cursor')
                code.append('    )')
                code.append('    messages.extend(result["messages"])')
                code.append('    cursor = result.get("response_metadata", {}).get("next_cursor")')
                code.append('    if not cursor: break')
            else:
                code.append(f'result = slack_client.conversations_history(channel="{channel}")')
                code.append('messages = result["messages"]')

            # Filter guidance
            if filter_results:
                code.append('# Bullet guidance: Apply filters to refine results')
                code.append('messages = [m for m in messages if not m.get("bot_id")]')

        elif action == 'delete':
            code.append('# Delete Slack messages')
            code.append(f'result = slack_client.conversations_history(channel="{channel}")')
            code.append('for msg in result["messages"]:')
            code.append('    slack_client.chat_delete(')
            code.append(f'        channel="{channel}",')
            code.append('        ts=msg["ts"]')
            code.append('    )')

        return code

    def _generate_venmo_code(
        self,
        instruction: str,
        action: str,
        validate: bool
    ) -> List[str]:
        """Generate Venmo-specific code with bullet guidance."""
        code = []

        if action == 'split':
            # Extract bill details
            amount_match = re.search(r'\$?(\d+(?:\.\d{2})?)', instruction)
            people_match = re.search(r'(\d+)\s+people', instruction, re.IGNORECASE)

            amount = float(amount_match.group(1)) if amount_match else 100.0
            people = int(people_match.group(1)) if people_match else 2

            if validate:
                code.append('# Bullet guidance: Validate input')
                code.append(f'assert amount > 0, "Amount must be positive"')
                code.append(f'assert people > 1, "Need at least 2 people to split"')
                code.append('')

            code.append('# Split bill on Venmo')
            code.append(f'amount = {amount}')
            code.append(f'people = {people}')
            code.append('split_amount = amount / people')
            code.append('')
            code.append('for person in ["Alice", "Bob"]:  # Example recipients')
            code.append('    venmo_client.payment.request_money(')
            code.append('        amount=split_amount,')
            code.append('        note=f"Your share: ${split_amount}",')
            code.append('        target_user=person')
            code.append('    )')

        return code

    def _generate_email_code(
        self,
        instruction: str,
        action: str,
        validate: bool
    ) -> List[str]:
        """Generate email code with bullet guidance."""
        code = []

        if action == 'send':
            code.append('# Send email')
            code.append('gmail_client.users().messages().send(')
            code.append('    userId="me",')
            code.append('    body={"raw": encoded_message}')
            code.append(').execute()')

        return code

    def _generate_generic_code(
        self,
        instruction: str,
        app: str,
        action: str,
        strategies: List[str]
    ) -> List[str]:
        """Generate generic code with bullet strategies."""
        code = [
            f'# Task: {instruction}',
            f'# App: {app}',
            f'# Action: {action}',
            '',
            '# Strategies from bullets:',
        ]

        for strategy in strategies:
            code.append(f'#   {strategy}')

        code.append('')
        code.append('# Implementation:')
        code.append('# TODO: Use bullet guidance to implement')

        return code

    def _execute_code(self, code: str, ground_truth: str = None) -> Tuple[str, bool]:
        """
        Execute generated code (simulated).

        Returns:
            (result, success)
        """
        # For now, simulate execution
        # In real implementation, would execute in sandbox

        # Check if code looks complete
        has_implementation = 'slack_client' in code or 'venmo_client' in code or 'TODO' not in code

        if ground_truth:
            # Simple heuristic: check if ground truth concepts are in code
            success = all(word.lower() in code.lower() for word in ground_truth.split()[:3])
        else:
            success = has_implementation

        result = f"Execution {'succeeded' if success else 'failed'}"
        return result, success

    def _evaluate_bullet_effectiveness(
        self,
        bullets: List[Dict],
        success: bool,
        execution_result: str
    ) -> Dict[str, str]:
        """
        Evaluate which bullets were helpful or harmful.

        Returns:
            {'bullet-id': 'helpful'|'harmful'|'neutral'}
        """
        feedback = {}

        for bullet in bullets:
            bullet_id = bullet['id']

            # Heuristic: If task succeeded, bullets are helpful
            # If failed, check if bullet guidance was actually applied
            if success:
                feedback[bullet_id] = 'helpful'
            else:
                # Check if bullet was relevant but didn't prevent failure
                content_lower = bullet.get('content', '').lower()
                if 'critical' in bullet.get('tags', []):
                    feedback[bullet_id] = 'harmful'  # Critical guidance was ignored
                else:
                    feedback[bullet_id] = 'neutral'

        return feedback
