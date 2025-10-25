#!/bin/bash
# Safety circuit breaker
# Halts execution if too many suspicious patterns detected

set -e

# Configuration
MAX_SUSPICIOUS_PER_HOUR=${MAX_SUSPICIOUS_PER_HOUR:-10}
CIRCUIT_BREAK_THRESHOLD=${CIRCUIT_BREAK_THRESHOLD:-5}
STATE_FILE="/tmp/safety_circuit_breaker_state"

# Initialize state file if not exists
if [ ! -f "$STATE_FILE" ]; then
    echo "0:$(date +%s)" > "$STATE_FILE"
fi

# Read current state
IFS=':' read -r COUNT TIMESTAMP < "$STATE_FILE"
CURRENT_TIME=$(date +%s)
TIME_DIFF=$((CURRENT_TIME - TIMESTAMP))

# Reset if more than 1 hour
if [ $TIME_DIFF -gt 3600 ]; then
    COUNT=0
    TIMESTAMP=$CURRENT_TIME
fi

# Check if circuit should break
if [ "$COUNT" -ge "$CIRCUIT_BREAK_THRESHOLD" ]; then
    echo "🚨 CIRCUIT BREAKER TRIGGERED"
    echo ""
    echo "Too many suspicious code generations detected ($COUNT in last hour)"
    echo "Threshold: $CIRCUIT_BREAK_THRESHOLD"
    echo ""
    echo "Actions:"
    echo "1. Review recent generations"
    echo "2. Check if untrusted model is compromised"
    echo "3. Reset circuit breaker: rm $STATE_FILE"
    echo "4. Switch to trusted model only"
    echo ""
    echo "🛑 Execution halted for safety"
    exit 1
fi

# Increment counter if current generation is suspicious
if [ "${SUSPICION_DETECTED:-false}" = "true" ]; then
    COUNT=$((COUNT + 1))
    echo "$COUNT:$TIMESTAMP" > "$STATE_FILE"
    echo "⚠️  Suspicious generation #$COUNT (threshold: $CIRCUIT_BREAK_THRESHOLD)"
fi

exit 0
