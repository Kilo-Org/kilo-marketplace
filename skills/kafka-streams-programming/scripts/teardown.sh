#!/usr/bin/env bash
# Clean up all resources for a Kafka Streams app.
# WARNING: This deletes topics and all data. Use with caution.
#
# Usage:
#   Local:           ./teardown.sh
#   Confluent Cloud: ./teardown.sh --cloud
#
# Customize the variables below to match your app.

set -euo pipefail

# ── Customize these ──────────────────────────────────────────────────────────
APP_ID="my-streams-app"              # Must match application.id in your config
INPUT_TOPICS=("input-events")        # Source topics your app reads from
OUTPUT_TOPICS=("output-events")      # Output topics your app writes to
STATE_DIR="/tmp/kafka-streams"       # Must match state.dir in your config

# Local connection
BOOTSTRAP_SERVER="localhost:9092"

if [[ -z "$APP_ID" || "$APP_ID" == -* || "$APP_ID" == *$'\n'* ]]; then
    echo "APP_ID must be non-empty and must not start with '-' or contain newlines." >&2
    exit 1
fi

# ── Parse arguments ──────────────────────────────────────────────────────────
USE_CLOUD=false
if [[ "${1:-}" == "--cloud" ]]; then
    USE_CLOUD=true
fi

# ── Confirmation ─────────────────────────────────────────────────────────────
echo "This will delete ALL topics and state for application: ${APP_ID}"
echo ""
echo "Topics to delete:"
for topic in "${INPUT_TOPICS[@]}" "${OUTPUT_TOPICS[@]}"; do
    echo "  - $topic"
done
for topic in "${INPUT_TOPICS[@]}"; do
    echo "  - ${APP_ID}-${topic}-dlq"
done
echo "  - Internal topics matching: ${APP_ID}-*"
echo ""
read -p "Continue? (y/N) " confirm
[[ "$confirm" == "y" ]] || exit 0

# ── Delete topics ────────────────────────────────────────────────────────────
delete_topic() {
    local topic="$1"
    echo "Deleting: $topic"
    if $USE_CLOUD; then
        confluent kafka topic delete "$topic" 2>/dev/null && echo "  Deleted." || echo "  Not found (OK)."
    else
        kafka-topics --delete --topic "$topic" --bootstrap-server "$BOOTSTRAP_SERVER" 2>/dev/null && echo "  Deleted." || echo "  Not found (OK)."
    fi
}

echo "=== Deleting application topics ==="
for topic in "${INPUT_TOPICS[@]}" "${OUTPUT_TOPICS[@]}"; do
    delete_topic "$topic"
done

echo ""
echo "=== Deleting DLQ topics ==="
for topic in "${INPUT_TOPICS[@]}"; do
    delete_topic "${APP_ID}-${topic}-dlq"
done

echo ""
echo "=== Deleting internal topics (changelog, repartition) ==="
if $USE_CLOUD; then
    confluent kafka topic list --output json 2>/dev/null | \
      jq -r '.[].name // empty' 2>/dev/null | \
      grep -F -- "${APP_ID}-" | \
      while read -r topic; do
        [[ "$topic" == "${APP_ID}-"* ]] && delete_topic "$topic"
      done || echo "  No internal topics found."
else
    kafka-topics --list --bootstrap-server "$BOOTSTRAP_SERVER" 2>/dev/null | \
      while read -r topic; do
        [[ "$topic" == "${APP_ID}-"* ]] && delete_topic "$topic"
      done || echo "  No internal topics found."
fi

echo ""
echo "=== Cleaning local state ==="
if [[ -d "${STATE_DIR}/${APP_ID}" ]]; then
    rm -rf "${STATE_DIR}/${APP_ID}"
    echo "  Deleted: ${STATE_DIR}/${APP_ID}"
else
    echo "  No local state found at ${STATE_DIR}/${APP_ID}"
fi

echo ""
echo "Done. All resources for ${APP_ID} have been cleaned up."
