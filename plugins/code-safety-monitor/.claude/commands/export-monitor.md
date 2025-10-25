# Export Monitor Command

Export the optimized monitor as a reusable Claude Skill for integration with other projects.

## Usage

```bash
/export-monitor --model models/gepa_optimized.json --output monitors/safety-monitor.skill [--include-weights]
```

## Arguments

- `--model`: Path to trained monitor model
- `--output`: Output path for Claude Skill
- `--include-weights`: Include fine-tuned weights (default: false)

## What Is a Claude Skill?

A Claude Skill is a portable, reusable AI workflow that can be:
- Loaded in any Claude Code session
- Shared across projects
- Version controlled
- Composed with other skills

## Example

```bash
# Export GEPA-optimized monitor
/export-monitor \
  --model models/gepa_optimized.json \
  --output monitors/safety-monitor-v1.skill

# Export with fine-tuned weights
/export-monitor \
  --model models/gepa_finetuned.json \
  --output monitors/safety-monitor-v1-ft.skill \
  --include-weights
```

## Output

```
Exporting monitor to Claude Skill...

Model: models/gepa_optimized.json
Output: monitors/safety-monitor-v1.skill

✓ Extracted optimized prompt
✓ Packaged configuration
✓ Generated skill manifest

Skill exported successfully!

Usage:
  claude skill load monitors/safety-monitor-v1.skill
  /scan-code your_code.py
```

## Using Exported Skills

### In Another Project

```bash
cd /path/to/another-project

# Load the skill
claude skill load /path/to/monitors/safety-monitor-v1.skill

# Use it
/scan-code src/api_handler.py
```

### Share with Team

```bash
# Commit skill to git
git add monitors/safety-monitor-v1.skill
git commit -m "Add trained safety monitor skill"
git push

# Teammate uses it
git pull
claude skill load monitors/safety-monitor-v1.skill
```

### Programmatic Usage

```python
from claude_code.skills import load_skill

# Load skill
monitor_skill = load_skill("monitors/safety-monitor-v1.skill")

# Use it
result = monitor_skill.run(
    command="scan-code",
    args={"file_path": "code.py"}
)
```

## Skill Contents

The exported skill includes:

```
safety-monitor-v1.skill/
├── manifest.json          # Skill metadata
├── prompt.txt             # GEPA-optimized prompt
├── config.json            # Model configuration
├── agents/                # Agent definitions
├── commands/              # Slash commands
└── weights.bin            # Fine-tuned weights (if --include-weights)
```

## Version Management

```bash
# Export different versions
/export-monitor --model models/gepa.json --output monitors/v1.0.skill
/export-monitor --model models/gepa_ft.json --output monitors/v1.1.skill

# Use specific version
claude skill load monitors/v1.1.skill
```

## Skill Manifest Example

```json
{
  "name": "code-safety-monitor",
  "version": "1.0.0",
  "description": "DSPy-powered backdoor detection monitor",
  "author": "your-team",
  "created": "2024-01-15T10:30:00Z",
  "model": {
    "base": "openai/gpt-4.1-nano-2025-04-14",
    "optimized": true,
    "method": "GEPA",
    "performance": {
      "safety_at_1pct": 0.90,
      "tpr": 0.90,
      "fpr": 0.01
    }
  },
  "commands": [
    "/scan-code"
  ]
}
```

## Publishing

Share your monitor with the community:

```bash
# Package for distribution
tar -czf safety-monitor-v1.tar.gz monitors/safety-monitor-v1.skill

# Publish to registry (future feature)
claude skill publish monitors/safety-monitor-v1.skill
```

## Related Commands

- `/optimize-gepa`: Create optimized monitor to export
- `/validate-safety`: Verify performance before export
