"""
AppWorld dataset loader for ACE benchmarking.

Loads task specifications from AppWorld benchmark data.
"""

import json
from pathlib import Path
from typing import List, Dict, Any


class AppWorldLoader:
    """
    Load AppWorld tasks from dataset splits.

    AppWorld format:
    - Split files contain task IDs (one per line)
    - Task specs are in data/tasks/{task_id}/specs.json
    """

    def __init__(self, data_root: str):
        """
        Args:
            data_root: Path to AppWorld data root (contains datasets/ and tasks/)
        """
        self.data_root = Path(data_root)
        self.datasets_dir = self.data_root / "datasets"
        self.tasks_dir = self.data_root / "tasks"

        if not self.datasets_dir.exists():
            raise FileNotFoundError(f"Datasets directory not found: {self.datasets_dir}")
        if not self.tasks_dir.exists():
            raise FileNotFoundError(f"Tasks directory not found: {self.tasks_dir}")

    def load_split(self, split_name: str, max_samples: int = None) -> List[Dict[str, Any]]:
        """
        Load samples from a dataset split.

        Args:
            split_name: Name of split (train, dev, test_normal, test_challenge)
            max_samples: Maximum number of samples to load (None = all)

        Returns:
            List of samples with format:
            [{
                'id': 'task_id',
                'instruction': 'Natural language instruction',
                'supervisor': {...},
                'datetime': '2023-05-18T12:00:00',
                'task_dir': Path to task directory
            }, ...]
        """
        split_file = self.datasets_dir / f"{split_name}.txt"

        if not split_file.exists():
            raise FileNotFoundError(f"Split file not found: {split_file}")

        # Read task IDs from split file
        with open(split_file, 'r') as f:
            task_ids = [line.strip() for line in f if line.strip()]

        if max_samples is not None:
            task_ids = task_ids[:max_samples]

        print(f"Loading {len(task_ids)} tasks from {split_name} split...")

        samples = []
        for task_id in task_ids:
            task_dir = self.tasks_dir / task_id
            specs_file = task_dir / "specs.json"

            if not specs_file.exists():
                print(f"⚠️  Warning: specs.json not found for task {task_id}, skipping")
                continue

            # Load task specification
            with open(specs_file, 'r') as f:
                specs = json.load(f)

            # Create sample in ACE format
            sample = {
                'id': task_id,
                'task_id': task_id,  # Also add as task_id for executor compatibility
                'instruction': specs.get('instruction', ''),
                'supervisor': specs.get('supervisor', {}),
                'datetime': specs.get('datetime', ''),
                'task_dir': str(task_dir),
                # Extract apps/APIs from instruction (simplified)
                'apps': self._extract_apps(specs.get('instruction', '')),
                'apis': [],
                # Ground truth placeholder (will be loaded during evaluation)
                'ground_truth': ''
            }

            samples.append(sample)

        print(f"✓ Loaded {len(samples)} samples from {split_name}")
        return samples

    def _extract_apps(self, instruction: str) -> List[str]:
        """
        Extract app names from instruction text.

        Simple heuristic: look for common app names in lowercase.
        """
        instruction_lower = instruction.lower()

        # Common AppWorld apps
        app_keywords = [
            'venmo', 'gmail', 'slack', 'contacts', 'calendar',
            'phone', 'messaging', 'email', 'notes', 'reminders'
        ]

        apps = []
        for app in app_keywords:
            if app in instruction_lower:
                apps.append(app)

        return apps if apps else ['general']

    def get_split_info(self) -> Dict[str, int]:
        """
        Get information about available splits.

        Returns:
            Dict mapping split name to sample count
        """
        info = {}
        for split_file in self.datasets_dir.glob("*.txt"):
            split_name = split_file.stem
            with open(split_file, 'r') as f:
                count = sum(1 for line in f if line.strip())
            info[split_name] = count

        return info


if __name__ == "__main__":
    # Test loader
    import sys
    from pathlib import Path

    # Add parent to path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    data_root = Path(__file__).parent.parent / "data"

    loader = AppWorldLoader(str(data_root))

    print("\n" + "="*70)
    print("AppWorld Dataset Info")
    print("="*70)

    info = loader.get_split_info()
    for split_name, count in sorted(info.items()):
        print(f"  {split_name:20s}: {count:4d} samples")

    print("\n" + "="*70)
    print("Loading train split (first 5 samples)")
    print("="*70)

    samples = loader.load_split('train', max_samples=5)

    for i, sample in enumerate(samples):
        print(f"\nSample {i+1}:")
        print(f"  ID: {sample['id']}")
        print(f"  Instruction: {sample['instruction'][:100]}...")
        print(f"  Apps: {sample['apps']}")
        print(f"  Supervisor: {sample['supervisor'].get('email', 'N/A')}")
