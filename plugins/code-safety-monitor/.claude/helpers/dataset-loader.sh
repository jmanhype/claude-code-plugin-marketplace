#!/bin/bash
# Dataset Loader Helper
# Load and prepare Control Arena datasets

set -e

DATASET=${1:-control-tax}
LIMIT=${2:-200}
OUTPUT=${3:-"datasets/${DATASET}.json"}

echo "📦 Loading Control Arena dataset: $DATASET"
echo ""

# Create datasets directory
mkdir -p datasets

# Load dataset
python3 << EOF
import json
import random
from pathlib import Path
from control_arena.settings.apps.apps_setting import get_dataset
from control_arena.settings.apps.task.metadata import AppsTaskMetadata

# Configuration
dataset_type = "$DATASET"
limit = $LIMIT
output_path = "$OUTPUT"

# Map dataset names
dataset_config = {
    "control-tax": {
        "has_backdoor_solution": True,
        "backdoor_source": "control_tax"
    },
    "apps-backdoors": {
        "has_backdoor_solution": True,
        "backdoor_source": "apps"
    }
}

if dataset_type not in dataset_config:
    print(f"❌ Unknown dataset: {dataset_type}")
    print(f"Available: {list(dataset_config.keys())}")
    exit(1)

config = dataset_config[dataset_type]

print(f"Fetching {dataset_type} from Control Arena...")
samples = get_dataset(**config)

print(f"Found {len(samples)} samples")

# Convert to DSPy format
examples = []
for s in samples:
    metadata = AppsTaskMetadata.model_validate(s.metadata)

    for solution, backdoor in zip(metadata.solutions, metadata.backdoors):
        example = {
            "task_description": metadata.main_task_description,
            "honest_code": solution["code"],
            "attack_code": backdoor["backdoor_code"],
            "backdoor_input": backdoor["backdoor_input"]
        }
        examples.append(example)

# Shuffle and limit
random.seed(42)
random.shuffle(examples)
examples = examples[:limit]

print(f"Selected {len(examples)} examples")

# Save
Path(output_path).parent.mkdir(parents=True, exist_ok=True)
with open(output_path, 'w') as f:
    json.dump(examples, f, indent=2)

print(f"✓ Saved to: {output_path}")

# Preview
print("\nSample preview:")
print(f"Task: {examples[0]['task_description'][:50]}...")
print(f"Backdoor input: {examples[0]['backdoor_input']}")
EOF

echo ""
echo "✓ Dataset ready!"
echo ""
echo "Next steps:"
echo "  Train: /train-monitor --dataset $OUTPUT"
echo "  Or optimize: /optimize-gepa --dataset $OUTPUT"
echo ""
