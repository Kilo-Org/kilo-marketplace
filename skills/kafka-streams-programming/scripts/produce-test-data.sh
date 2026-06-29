#!/usr/bin/env bash
# Produce test data to a Kafka topic using the console producer.
# Customize the variables and sample records below for your app.
#
# Usage:
#   ./produce-test-data.sh
#
# For Avro data, use kafka-avro-console-producer instead (requires Schema Registry).

set -euo pipefail

# ── Customize these ──────────────────────────────────────────────────────────
TOPIC="input-events"
BOOTSTRAP_SERVER="localhost:9092"
SCHEMA_REGISTRY="http://localhost:8081"

# Set to "avro" for Avro-encoded data, "json" for plain JSON
FORMAT="avro"

# ── Avro schema (inline, must match your .avsc file) ─────────────────────────
# Replace with your actual schema
AVRO_SCHEMA='{
  "type": "record",
  "name": "InputEvent",
  "namespace": "com.example",
  "fields": [
    {"name": "id", "type": "string"},
    {"name": "value", "type": "string"},
    {"name": "timestamp", "type": {"type": "long", "logicalType": "timestamp-millis"}}
  ]
}'

# ── Sample records (one per line, JSON format) ───────────────────────────────
# Replace with records matching your schema
RECORDS='{"id":"1","value":"test-event-1","timestamp":1710000000000}
{"id":"2","value":"test-event-2","timestamp":1710000001000}
{"id":"3","value":"test-event-3","timestamp":1710000002000}
{"id":"4","value":"invalid-event","timestamp":1710000003000}
{"id":"5","value":"test-event-5","timestamp":1710000004000}'

# ── Produce ──────────────────────────────────────────────────────────────────
echo "Producing test data to topic: $TOPIC"
echo ""

if [[ "$FORMAT" == "avro" ]]; then
    echo "$RECORDS" | kafka-avro-console-producer \
        --topic "$TOPIC" \
        --bootstrap-server "$BOOTSTRAP_SERVER" \
        --property schema.registry.url="$SCHEMA_REGISTRY" \
        --property value.schema="$AVRO_SCHEMA"
else
    echo "$RECORDS" | kafka-console-producer \
        --topic "$TOPIC" \
        --bootstrap-server "$BOOTSTRAP_SERVER"
fi

echo ""
echo "Produced $(echo "$RECORDS" | wc -l | tr -d ' ') records to $TOPIC"
