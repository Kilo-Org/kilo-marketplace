# CLI Commands Reference

Explicit CLI commands for every operation. The agent should copy-paste from here, not guess syntax.

## Prerequisites

### Confluent Cloud

```bash
# Install confluent CLI (macOS)
brew install confluentinc/tap/cli
# Other platforms: https://docs.confluent.io/confluent-cli/current/install.md

# Log in (interactive — opens browser)
confluent login
# Or persist credentials:
confluent login --save

# Verify login
confluent kafka cluster list

# Select environment and cluster
confluent environment list
confluent environment use <env-id>
confluent kafka cluster list
confluent kafka cluster use <cluster-id>
```

**IMPORTANT: CLI auth vs App auth are SEPARATE mechanisms.**
- The `confluent` CLI uses your **login session** for management operations (creating topics, consuming, listing, etc.).
- The **API key/secret** in `.env` is for the **application** to authenticate via SASL_SSL at runtime.
- Do NOT try to pass `--api-key` to topic management commands — that flag does not exist.
- `confluent api-key store` is only needed if you want to associate a key with a cluster for later use — it does NOT affect CLI login auth.

### Confluent Platform

```bash
# Tools are in $CONFLUENT_HOME/bin/
# Verify:
which kafka-topics
# If not found, add to PATH:
export PATH=$CONFLUENT_HOME/bin:$PATH
```

### Apache Kafka (Open Source)

```bash
# Download from https://kafka.apache.org/downloads
# Tools are in the extracted bin/ directory
# Verify:
which kafka-topics.sh
# If not found, add to PATH:
export PATH=/path/to/kafka/bin:$PATH
```

## Topic Management

| Operation | Confluent Cloud | CP / Apache Kafka |
|-----------|----------------|-------------------|
| List | `confluent kafka topic list` | `kafka-topics --list --bootstrap-server localhost:9092` |
| Create | `confluent kafka topic create <topic> --partitions <N>` | `kafka-topics --create --topic <topic> --partitions <N> --replication-factor <R> --bootstrap-server localhost:9092 --if-not-exists` |
| Delete | `confluent kafka topic delete <topic>` | `kafka-topics --delete --topic <topic> --bootstrap-server localhost:9092` |
| Describe | `confluent kafka topic describe <topic>` | `kafka-topics --describe --topic <topic> --bootstrap-server localhost:9092` |

**Create with config (CC):** Add `--config retention.ms=604800000`

## Consuming (for verification)

**Confluent Cloud:**
```bash
confluent kafka topic consume <topic> --from-beginning --print-key \
  --value-format <avro|protobuf|jsonschema> \
  --schema-registry-endpoint <SR_URL> \
  --schema-registry-api-key <SR_KEY> \
  --schema-registry-api-secret <SR_SECRET>
```
Omit `--value-format` and SR flags for plain text.

**CP / Apache Kafka:**

| Format | Command |
|--------|---------|
| Avro | `kafka-avro-console-consumer --bootstrap-server localhost:9092 --topic <topic> --from-beginning --property schema.registry.url=http://localhost:8081 --property print.key=true --key-deserializer org.apache.kafka.common.serialization.StringDeserializer` |
| Protobuf | `kafka-protobuf-console-consumer` (same args) |
| JSON Schema | `kafka-json-schema-console-consumer` (same args) |

> The `--key-deserializer` override is required because these schema-aware consumers default `KafkaAvroDeserializer` (or equivalent) for the key, but our topologies write string keys with `Serdes.String()` — a raw UTF-8 key has no `0x00` magic byte + 4-byte schema ID, so the schema deserializer fails on the first record.

## Producing Test Data

### Confluent Cloud

```bash
# Avro (inline schema)
confluent kafka topic produce <topic> --value-format avro \
  --schema '<avro-schema-json>'

# Avro (schema file)
confluent kafka topic produce <topic> --value-format avro \
  --schema @path/to/schema.avsc

# With key
confluent kafka topic produce <topic> --value-format avro \
  --schema '<avro-schema-json>' --parse-key --delimiter ':'
```

### Confluent Platform / Apache Kafka

```bash
# Avro
kafka-avro-console-producer --bootstrap-server localhost:9092 \
  --topic <topic> --property schema.registry.url=http://localhost:8081 \
  --property value.schema='<avro-schema-json>'
```

**Never use plain `kafka-console-producer` for schematized topics** — it produces raw strings without the Schema Registry magic byte, causing `Unknown magic byte!` deserialization errors.

## Schema Registry

### Confluent Cloud

```bash
# List subjects
confluent schema-registry subject list

# Describe a subject (get schema)
confluent schema-registry subject describe <topic-name>-value

# List versions
confluent schema-registry subject list --subject-prefix <topic-name>
```

### Confluent Platform / Apache Kafka (REST API)

```bash
# List subjects
curl http://localhost:8081/subjects

# Get latest schema for a subject
curl http://localhost:8081/subjects/<topic-name>-value/versions/latest

# With auth (CC or secured CP)
curl -u <SR_KEY>:<SR_SECRET> <SR_URL>/subjects
```

## API Key Management (Confluent Cloud only)

```bash
# Create a Kafka cluster API key
confluent api-key create --resource <cluster-id>

# Create a Schema Registry API key
confluent api-key create --resource <sr-cluster-id>

# Store an API key locally (if key wasn't created via CLI)
confluent api-key store <KEY> <SECRET> --resource <cluster-id>

# List API keys
confluent api-key list --resource <cluster-id>
```

## Application Reset

```bash
# The reset tool ships with Apache Kafka / Confluent Platform
# Download Apache Kafka if you don't have it: https://kafka.apache.org/downloads

# Basic reset (local, no auth)
kafka-streams-application-reset \
  --application-id <app-id> \
  --bootstrap-server localhost:9092 \
  --input-topics <topic1>,<topic2>

# Reset with auth (CC or secured CP)
kafka-streams-application-reset \
  --application-id <app-id> \
  --bootstrap-server <bootstrap-servers> \
  --input-topics <topic1>,<topic2> \
  --command-config client.properties
```

### client.properties for CC reset

```properties
security.protocol=SASL_SSL
sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required \
  username='<CLUSTER_API_KEY>' password='<CLUSTER_API_SECRET>';
```
