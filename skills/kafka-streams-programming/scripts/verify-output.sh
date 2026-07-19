#!/usr/bin/env bash
# Consume and display records from an output topic.
# Use this to verify your Kafka Streams app is producing expected results.
#
# Usage:
#   ./verify-output.sh                    # Read from beginning, exit after 10s idle
#   ./verify-output.sh --topic my-topic   # Specify a different topic
#   ./verify-output.sh --count 5          # Exit after reading 5 records

set -euo pipefail

# ── Defaults ─────────────────────────────────────────────────────────────────
TOPIC="output-events"
BOOTSTRAP_SERVER="localhost:9092"
SCHEMA_REGISTRY="http://localhost:8081"
FORMAT="avro"          # "avro" or "json"
MAX_MESSAGES=""        # Empty = read until timeout
TIMEOUT_MS=10000       # Exit after 10s with no new messages

# ── Parse arguments ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --topic) TOPIC="$2"; shift 2 ;;
        --count) MAX_MESSAGES="$2"; shift 2 ;;
        --timeout) TIMEOUT_MS="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ── Consume ──────────────────────────────────────────────────────────────────
echo "Consuming from topic: $TOPIC"
echo "Format: $FORMAT"
echo "Press Ctrl+C to stop"
echo "────────────────────────────────────────"

MAX_MSG_FLAG=""
if [[ -n "$MAX_MESSAGES" ]]; then
    MAX_MSG_FLAG="--max-messages $MAX_MESSAGES"
fi

if [[ "$FORMAT" == "avro" ]]; then
    # shellcheck disable=SC2086
    kafka-avro-console-consumer \
        --topic "$TOPIC" \
        --bootstrap-server "$BOOTSTRAP_SERVER" \
        --property schema.registry.url="$SCHEMA_REGISTRY" \
        --property print.key=true \
        --property key.separator=" | " \
        --key-deserializer org.apache.kafka.common.serialization.StringDeserializer \
        --from-beginning \
        --timeout-ms "$TIMEOUT_MS" \
        $MAX_MSG_FLAG
else
    # shellcheck disable=SC2086
    kafka-console-consumer \
        --topic "$TOPIC" \
        --bootstrap-server "$BOOTSTRAP_SERVER" \
        --property print.key=true \
        --property key.separator=" | " \
        --from-beginning \
        --timeout-ms "$TIMEOUT_MS" \
        $MAX_MSG_FLAG
fi

echo "────────────────────────────────────────"
echo "Done."
