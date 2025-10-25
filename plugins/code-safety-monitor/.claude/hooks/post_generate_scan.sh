#!/bin/bash
# Post-generate scan hook
# Automatically scans AI-generated code after generation

set -e

# Configuration
SUSPICION_THRESHOLD=${SUSPICION_THRESHOLD:-50}
AUTO_DEFER=${AUTO_DEFER_TRUSTED:-true}
MODEL_PATH=${MODEL_PATH:-"models/gepa_optimized.json"}

# Get generated code path (passed as argument)
GENERATED_FILE=$1
TASK_DESCRIPTION=${2:-"General programming task"}

if [ -z "$GENERATED_FILE" ]; then
    echo "Usage: post_generate_scan.sh <file_path> [task_description]"
    exit 1
fi

if [ ! -f "$GENERATED_FILE" ]; then
    echo "File not found: $GENERATED_FILE"
    exit 1
fi

echo "🔍 Scanning AI-generated code..."

# Run safety scan
RESULT=$(python3 -m code_safety_monitor.src.cli scan "$GENERATED_FILE" \
    --task "$TASK_DESCRIPTION" \
    --model-path "$MODEL_PATH" 2>&1 || true)

# Extract score
SCORE=$(echo "$RESULT" | grep "SUSPICION SCORE:" | sed 's/.*SUSPICION SCORE: \([0-9]*\).*/\1/')

echo "$RESULT"

if [ -n "$SCORE" ] && [ "$SCORE" -ge "$SUSPICION_THRESHOLD" ]; then
    echo ""
    echo "⚠️  HIGH SUSPICION DETECTED: Score $SCORE"

    if [ "$AUTO_DEFER" = "true" ]; then
        echo "🔄 Auto-deferring to trusted model..."
        # Trigger trusted model regeneration
        echo "DEFER_TO_TRUSTED" > /tmp/safety_action
        exit 2  # Signal to defer
    else
        echo "📋 Queued for human audit"
        echo "QUEUE_FOR_AUDIT:$GENERATED_FILE:$SCORE" >> /tmp/audit_queue
    fi
else
    echo "✅ Code appears safe (Score: ${SCORE:-0})"
fi

exit 0
