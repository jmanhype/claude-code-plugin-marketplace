# Backdoor Detection Pipeline

End-to-end pipeline for detecting backdoors in code using DSPy monitors.

## Pipeline Overview

```
Input Code → Monitor → Score → Route → [Approve | Audit | Defer]
```

## Quick Start

```bash
# 1. Single file scan
/scan-code suspicious_code.py

# 2. Batch scan directory
for file in src/**/*.py; do
    /scan-code "$file" --threshold 50
done

# 3. Continuous monitoring (via hooks)
# Automatically scans all AI-generated code
```

## Pipeline Components

### 1. Input Processing
- Load code files
- Extract task context
- Prepare for monitoring

### 2. DSPy Monitor
- Chain of Thought reasoning
- GEPA-optimized prompts
- Fine-grained scoring (0-100)

### 3. Classification
- **Low (0-49)**: Approve automatically
- **Medium (50-79)**: Queue for human audit
- **High (80-100)**: Auto-defer to trusted model

### 4. Action Routing
```python
if score >= 80:
    defer_to_trusted()
elif score >= 50:
    queue_for_audit()
else:
    approve()
```

## Batch Processing

```bash
#!/bin/bash
# batch_scan.sh

THRESHOLD=50
RESULTS_FILE="scan_results.json"

echo "[" > $RESULTS_FILE

for FILE in $(find src -name "*.py"); do
    RESULT=$(/scan-code "$FILE" --threshold $THRESHOLD --format json)
    echo "$RESULT," >> $RESULTS_FILE
done

echo "]" >> $RESULTS_FILE

# Analyze results
cat $RESULTS_FILE | jq '[.[] | select(.score >= 50)]'
```

## Integration with CI/CD

```yaml
# .github/workflows/safety-check.yml
name: Safety Check
on: [pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Install monitor
        run: |
          pip install -r requirements.txt
          /plugin install code-safety-monitor

      - name: Scan changed files
        run: |
          for file in $(git diff --name-only origin/main); do
            /scan-code "$file" --threshold 50 || exit 1
          done
```

## Real-time Monitoring

```python
# Live monitoring during development
from watchdog.observers import Observer
from code_safety_monitor.src import create_monitor

monitor = create_monitor()

class CodeSafetyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            score, reasoning = monitor.scan_code(
                open(event.src_path).read(),
                "Development code"
            )
            if score >= 50:
                notify_developer(event.src_path, score)

observer = Observer()
observer.schedule(CodeSafetyHandler(), 'src/', recursive=True)
observer.start()
```

## Performance Optimization

- **Parallel Processing**: Scan multiple files concurrently
- **Caching**: Cache results for unchanged files
- **Incremental**: Only scan modified code
- **Async**: Use `aforward()` for async processing

## Metrics Collection

```bash
# Track detection rates
cat logs/detections.log | \
  jq -s 'group_by(.date) | map({
    date: .[0].date,
    total: length,
    flagged: [.[] | select(.score >= 50)] | length,
    rate: ([.[] | select(.score >= 50)] | length) / length
  })'
```

## Related Workflows

- **ai-control-monitoring**: Full control protocol
- **safety-training-loop**: Continuous improvement
- **vulnerability-assessment**: Security scanning
