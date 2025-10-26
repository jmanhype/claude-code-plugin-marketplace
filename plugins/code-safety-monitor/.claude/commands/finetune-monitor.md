# Finetune Monitor Command

Bootstrap fine-tune the monitor after GEPA optimization to further improve performance.

## Usage

```bash
/finetune-monitor --base-model models/gepa_optimized.json --dataset control_tax.json [--samples 200]
```

## When to Finetune

- **After GEPA optimization** (not before!)
- When you need the absolute best performance
- For production deployments
- When audit budget is very tight (<0.5%)

## What It Does

1. Loads GEPA-optimized monitor
2. Generates predictions on training set
3. Filters for correct predictions (attack > honest)
4. Creates fine-tuning dataset from trajectories
5. Fine-tunes model weights via OpenAI API
6. Saves fine-tuned model

## Example

```bash
/finetune-monitor \
  --base-model models/gepa_optimized.json \
  --dataset datasets/control_tax.json \
  --samples 200
```

## Output

```
Loading GEPA-optimized model...
Generating predictions on 200 samples...
Filtering correct predictions: 178/200 (89%)

Creating fine-tuning dataset...
Uploading to OpenAI...
Starting fine-tuning job: ftjob-abc123...

[Progress: ████████████████░░░░] 80%

Fine-tuning complete!
Model: ft:gpt-4.1-nano-2025-04-14:abc123
Saved to: models/gepa_finetuned.json
```

## Performance Impact

```
GEPA Only:
  Safety @ 0.5%: 80%
  Safety @ 1.0%: 90%

GEPA + Finetune:
  Safety @ 0.5%: 85%  (+5%)
  Safety @ 1.0%: 90%  (same)
```

Fine-tuning helps most at very low audit budgets.

## Cost Considerations

- GEPA: ~$5-10 (API calls for reflection)
- Fine-tuning: ~$50-100 (model training)

Use GEPA first, only finetune if needed.

## Programmatic Usage

```python
from code_safety_monitor.src.trainer import FinetuneTrainer, train_pipeline

# Full pipeline with fine-tuning
monitor = train_pipeline(
    trainset=train_examples,
    run_finetune=True  # Enable fine-tuning
)
```

## Related Commands

- `/optimize-gepa`: Run this first
- `/validate-safety`: Evaluate fine-tuned model
