#!/bin/bash
# Pre-commit safety hook
# Scans code for backdoors before allowing commits

set -e

# Configuration
SUSPICION_THRESHOLD=${SUSPICION_THRESHOLD:-50}
MODEL_PATH=${MODEL_PATH:-"models/gepa_optimized.json"}
BLOCK_ON_HIGH_SUSPICION=${BLOCK_ON_HIGH_SUSPICION:-true}

# Get staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|js|ts|java|cpp|c|go)$' || true)

if [ -z "$STAGED_FILES" ]; then
    echo "✓ No code files to scan"
    exit 0
fi

echo "🔍 Scanning staged files for backdoors..."

# Scan each file
HIGH_SUSPICION_FILES=()
TOTAL_SCANNED=0

for FILE in $STAGED_FILES; do
    TOTAL_SCANNED=$((TOTAL_SCANNED + 1))

    # Run safety scan
    RESULT=$(python3 -m code_safety_monitor.src.cli scan "$FILE" --model-path "$MODEL_PATH" 2>&1 || true)

    # Extract suspicion score
    SCORE=$(echo "$RESULT" | grep "SUSPICION SCORE:" | sed 's/.*SUSPICION SCORE: \([0-9]*\).*/\1/')

    if [ -n "$SCORE" ] && [ "$SCORE" -ge "$SUSPICION_THRESHOLD" ]; then
        echo "⚠️  $FILE: Score $SCORE (FLAGGED)"
        HIGH_SUSPICION_FILES+=("$FILE:$SCORE")
    else
        echo "✓ $FILE: Score ${SCORE:-0} (SAFE)"
    fi
done

# Report results
echo ""
echo "Scanned $TOTAL_SCANNED files"

if [ ${#HIGH_SUSPICION_FILES[@]} -gt 0 ]; then
    echo ""
    echo "❌ HIGH SUSPICION FILES DETECTED:"
    for ITEM in "${HIGH_SUSPICION_FILES[@]}"; do
        echo "  - $ITEM"
    done

    if [ "$BLOCK_ON_HIGH_SUSPICION" = "true" ]; then
        echo ""
        echo "🚫 COMMIT BLOCKED: Remove suspicious code or override with:"
        echo "   BLOCK_ON_HIGH_SUSPICION=false git commit"
        exit 1
    else
        echo ""
        echo "⚠️  WARNING: Committing despite high suspicion"
    fi
fi

echo "✓ Safety check passed"
exit 0
