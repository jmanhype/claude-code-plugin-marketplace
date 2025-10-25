#!/bin/bash
# GEPA Trainer Helper
# Quick script to run GEPA optimization

set -e

# Configuration
TRAIN_SAMPLES=${TRAIN_SAMPLES:-200}
VAL_SAMPLES=${VAL_SAMPLES:-100}
MAX_EVALS=${MAX_EVALS:-2}
DATASET=${DATASET:-"datasets/control_tax.json"}
OUTPUT_DIR=${OUTPUT_DIR:-"models"}

echo "🚀 Starting GEPA Optimization"
echo ""
echo "Configuration:"
echo "  Train samples: $TRAIN_SAMPLES"
echo "  Val samples: $VAL_SAMPLES"
echo "  Max evaluations: $MAX_EVALS"
echo "  Dataset: $DATASET"
echo "  Output: $OUTPUT_DIR"
echo ""

# Check dataset exists
if [ ! -f "$DATASET" ]; then
    echo "❌ Dataset not found: $DATASET"
    echo "Run: /load-control-arena --dataset control-tax --output $DATASET"
    exit 1
fi

# Check API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY not set"
    exit 1
fi

# Run GEPA optimization
python3 << EOF
from pathlib import Path
from code_safety_monitor.src import CodeSafetyMonitor
from code_safety_monitor.src.trainer import train_pipeline
from code_safety_monitor.src.utils import load_examples_from_json, split_dataset

# Load data
print("Loading dataset...")
examples = load_examples_from_json(Path("$DATASET"))
print(f"Loaded {len(examples)} examples")

# Split
splits = split_dataset(examples, train_ratio=0.67, val_ratio=0.33)
trainset = splits['train'][:$TRAIN_SAMPLES]
valset = splits['val'][:$VAL_SAMPLES]

print(f"Train: {len(trainset)}, Val: {len(valset)}")

# Run optimization
print("\nStarting GEPA optimization...")
monitor = train_pipeline(
    trainset=trainset,
    valset=valset,
    output_dir=Path("$OUTPUT_DIR"),
    run_finetune=False
)

print("\n✓ GEPA optimization complete!")
print(f"Model saved to: $OUTPUT_DIR/gepa_optimized.json")
EOF

echo ""
echo "🎉 Training complete!"
echo ""
echo "Next steps:"
echo "  1. Validate: /validate-safety --model $OUTPUT_DIR/gepa_optimized.json"
echo "  2. (Optional) Finetune: /finetune-monitor --base-model $OUTPUT_DIR/gepa_optimized.json"
echo "  3. Deploy: Use in /scan-code with --model-path flag"
echo ""
