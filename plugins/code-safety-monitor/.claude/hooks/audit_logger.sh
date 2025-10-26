#!/bin/bash
# Audit logger
# Logs all safety decisions for compliance and auditing

set -e

# Configuration
AUDIT_LOG_DIR=${AUDIT_LOG_DIR:-"logs/safety_audits"}
AUDIT_LOG_FILE="$AUDIT_LOG_DIR/audit_$(date +%Y%m%d).log"

# Create log directory
mkdir -p "$AUDIT_LOG_DIR"

# Get event details
EVENT_TYPE=${1:-"scan"}
FILE_PATH=${2:-"unknown"}
SUSPICION_SCORE=${3:-0}
DECISION=${4:-"pending"}

# Create log entry
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
LOG_ENTRY=$(cat <<EOF
{
  "timestamp": "$TIMESTAMP",
  "event_type": "$EVENT_TYPE",
  "file_path": "$FILE_PATH",
  "suspicion_score": $SUSPICION_SCORE,
  "decision": "$DECISION",
  "user": "${USER:-unknown}",
  "session_id": "${CLAUDE_SESSION_ID:-unknown}"
}
EOF
)

# Append to log file
echo "$LOG_ENTRY" >> "$AUDIT_LOG_FILE"

# Also log to structured format for analysis
echo "$TIMESTAMP,$EVENT_TYPE,$FILE_PATH,$SUSPICION_SCORE,$DECISION,$USER" >> "$AUDIT_LOG_DIR/audit.csv"

# Print confirmation
if [ "${VERBOSE_LOGGING:-false}" = "true" ]; then
    echo "📝 Logged safety event: $EVENT_TYPE ($FILE_PATH, score: $SUSPICION_SCORE)"
fi

exit 0
