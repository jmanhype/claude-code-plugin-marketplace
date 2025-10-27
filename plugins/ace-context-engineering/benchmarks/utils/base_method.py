"""
Base class for adaptive methods in ACE framework.
Defines the interface for Generator → Reflector → Curator workflow.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any


class AdaptiveMethod(ABC):
    """
    Abstract base class for adaptive methods.

    Implements the ACE cycle:
    1. Generate: Solve task using retrieved bullets
    2. Reflect: Analyze outcome and propose delta
    3. Curate: Validate and merge delta into playbook
    4. Adapt: Iterate over training data
    """

    def __init__(self, name: str):
        self.name = name
        self.playbook = None
        self.metrics = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'bullets_added': 0,
            'bullets_updated': 0,
        }

    @abstractmethod
    def generate(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate solution for a task using retrieved bullets.

        Args:
            sample: Task sample with 'instruction', 'apps', 'apis', etc.

        Returns:
            {
                'prediction': solution_string,
                'used_bullet_ids': [...],
                'bullet_feedback': {'bullet-123': 'helpful', ...},
                'observations': [...]
            }
        """
        pass

    @abstractmethod
    def reflect(self, sample: Dict, prediction: str, ground_truth: str, success: bool) -> Dict:
        """
        Reflect on task outcome and propose delta updates.

        Args:
            sample: Original task sample
            prediction: Generated solution
            ground_truth: Expected answer
            success: Whether task succeeded

        Returns:
            {
                'new_bullets': [...],
                'counters': [{'id': 'bullet-123', 'helpful_delta': 1}, ...],
                'edits': [...],
                'reasoning': '...'
            }
        """
        pass

    @abstractmethod
    def curate(self, delta: Dict) -> Dict:
        """
        Validate and normalize delta before merging.

        Args:
            delta: Proposed delta from reflect()

        Returns:
            {
                'clean_delta': {...},
                'curation_notes': '...',
                'requires_human_review': bool
            }
        """
        pass

    def adapt(self, samples: List[Dict], mode: str = 'offline', max_epochs: int = 5) -> Dict:
        """
        Run adaptation loop over training samples.

        Args:
            samples: List of task samples
            mode: 'offline' (train split) or 'online' (sequential test)
            max_epochs: Number of epochs for offline mode

        Returns:
            Evaluation metrics
        """
        if mode == 'offline':
            return self._adapt_offline(samples, max_epochs)
        elif mode == 'online':
            return self._adapt_online(samples)
        else:
            raise ValueError(f"Unknown mode: {mode}")

    @abstractmethod
    def _adapt_offline(self, samples: List[Dict], max_epochs: int) -> Dict:
        """
        Offline adaptation: Multi-epoch training on train split.
        """
        pass

    @abstractmethod
    def _adapt_online(self, samples: List[Dict]) -> Dict:
        """
        Online adaptation: Sequential test-time learning.
        """
        pass

    def load_playbook(self, playbook_path: str):
        """Load playbook from JSON file."""
        import json
        from pathlib import Path

        with open(playbook_path, 'r', encoding='utf-8') as f:
            self.playbook = json.load(f)

    def save_playbook(self, output_path: str):
        """Save updated playbook to JSON file."""
        import json
        from pathlib import Path

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.playbook, f, indent=2)

    def get_metrics(self) -> Dict:
        """Return current metrics with computed success rate."""
        metrics = self.metrics.copy()

        # Compute success rate
        if metrics['total_tasks'] > 0:
            metrics['success_rate'] = metrics['successful_tasks'] / metrics['total_tasks']
        else:
            metrics['success_rate'] = 0.0

        return metrics
