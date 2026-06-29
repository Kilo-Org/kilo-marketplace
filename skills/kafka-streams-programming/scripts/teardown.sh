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

STATE_DIR_ABS="$(realpath -m -- "$STATE_DIR")"
STATE_PATH="$(realpath -m -- "${STATE_DIR_ABS}/${APP_ID}")"
if [[ "$STATE_DIR_ABS" == "/" || "$STATE_DIR_ABS" == "$HOME" ||
      "$STATE_PATH" == "/" || "$STATE_PATH" == "$HOME" ||
      "$STATE_PATH" != "${STATE_DIR_ABS}/"* ]]; then
    echo "Refusing unsafe state path: ${STATE_PATH}" >&2
    exit 1
fi

# ── Parse arguments ──────────────────────────────────────────────────────────
USE_CLOUD=false
if [[ "${1:-}" == "--cloud" ]]; then
    USE_CLOUD=true
fi

# ── Discover exact internal topics ───────────────────────────────────────────
INTERNAL_TOPICS=()
if $USE_CLOUD; then
    while IFS= read -r topic; do
        INTERNAL_TOPICS+=("$topic")
    done < <(
        confluent kafka topic list --output json 2>/dev/null |
        jq -r '.[].name // empty' 2>/dev/null |
        grep -F -- "${APP_ID}-" || true
    )
else
    while IFS= read -r topic; do
        INTERNAL_TOPICS+=("$topic")
    done < <(
        kafka-topics --list --bootstrap-server "$BOOTSTRAP_SERVER" 2>/dev/null |
        grep -F -- "${APP_ID}-" || true
    )
fi

for topic in "${INTERNAL_TOPICS[@]}"; do
    [[ "$topic" == "${APP_ID}-"* ]] || {
        echo "Refusing unexpected internal topic: $topic" >&2
        exit 1
    }
done

# ── Confirmation ─────────────────────────────────────────────────────────────
echo "This will delete ALL listed topics and local state for application: ${APP_ID}"
echo ""
echo "Topics to delete:"
for topic in "${INPUT_TOPICS[@]}" "${OUTPUT_TOPICS[@]}"; do
    echo "  - $topic"
done
for topic in "${INPUT_TOPICS[@]}"; do
    echo "  - ${APP_ID}-${topic}-dlq"
done
for topic in "${INTERNAL_TOPICS[@]}"; do
    echo "  - $topic"
done
echo "Local state to delete: ${STATE_PATH}"
echo ""
read -r -p "Type DELETE ${APP_ID} to continue: " confirm
[[ "$confirm" == "DELETE ${APP_ID}" ]] || exit 0

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
if [[ ${#INTERNAL_TOPICS[@]} -eq 0 ]]; then
    echo "  No internal topics found."
else
    for topic in "${INTERNAL_TOPICS[@]}"; do
        delete_topic "$topic"
    done
fi

echo ""
echo "=== Cleaning local state ==="
if [[ -d "$STATE_PATH" ]]; then
    rm -rf -- "$STATE_PATH"
    echo "  Deleted: $STATE_PATH"
else
    echo "  No local state found at $STATE_PATH"
fi

echo ""
echo "Done. All resources for ${APP_ID} have been cleaned up."
