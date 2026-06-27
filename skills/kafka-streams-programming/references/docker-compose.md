# Docker Compose for Local Kafka Streams Development

Generate this `docker-compose.yml` for local development. It provides a single-node Kafka broker with Schema Registry — everything needed to run and test a Kafka Streams application locally.

## Docker Compose Template

```yaml
services:
  broker:
    image: confluentinc/confluent-local:8.2.0
    hostname: broker
    container_name: broker
    ports:
      - "9092:9092"   # Kafka clients
      - "8082:8082"   # REST Proxy (optional, for debugging)
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: 'CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT'
      KAFKA_ADVERTISED_LISTENERS: 'PLAINTEXT://broker:29092,PLAINTEXT_HOST://localhost:9092'
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_JMX_PORT: 9101
      KAFKA_JMX_HOSTNAME: localhost
      KAFKA_PROCESS_ROLES: 'broker,controller'
      KAFKA_CONTROLLER_QUORUM_VOTERS: '1@broker:29093'
      KAFKA_LISTENERS: 'PLAINTEXT://broker:29092,CONTROLLER://broker:29093,PLAINTEXT_HOST://0.0.0.0:9092'
      KAFKA_INTER_BROKER_LISTENER_NAME: 'PLAINTEXT'
      KAFKA_CONTROLLER_LISTENER_NAMES: 'CONTROLLER'
      KAFKA_LOG_DIRS: '/tmp/kraft-combined-logs'
      # Replace CLUSTER_ID with a unique base64 UUID using "bin/kafka-storage.sh random-uuid"
      # See https://docs.confluent.io/kafka/operations-tools/kafka-tools.md#kafka-storage-sh
      CLUSTER_ID: 'MkU3OEVBNTcwNTJENDM2Qk'

  schema-registry:
    image: confluentinc/cp-schema-registry:8.2.0
    hostname: schema-registry
    container_name: schema-registry
    depends_on:
      - broker
    ports:
      - "8081:8081"
    environment:
      SCHEMA_REGISTRY_HOST_NAME: schema-registry
      SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS: broker:29092
      SCHEMA_REGISTRY_LISTENERS: http://0.0.0.0:8081
```

## Local Development Properties

When running against the local Docker Compose environment, use these connection settings:

```properties
bootstrap.servers=localhost:9092
schema.registry.url=http://localhost:8081
auto.register.schemas=true

# No security needed for local dev
# security.protocol is not set (defaults to PLAINTEXT)
```

## Starting the Environment

Add these instructions to the generated README:

```bash
# Start Kafka and Schema Registry
docker compose up -d

# Verify services are running
docker compose ps

# Create input/output topics (recommended even though auto.create.topics.enable=true by default on local broker)
# Use --if-not-exists so the command is idempotent
docker exec broker kafka-topics --create --if-not-exists --topic input-topic --partitions 4 --replication-factor 1 --bootstrap-server localhost:9092
docker exec broker kafka-topics --create --if-not-exists --topic output-topic --partitions 4 --replication-factor 1 --bootstrap-server localhost:9092

# Run the Streams app
./gradlew run

# Produce test data (use schema-aware producer — ALL data is schematized)
# Replace the --property value.schema with your topic's Avro schema.
# For other formats, use kafka-json-schema-console-producer or kafka-protobuf-console-producer.
docker exec -i schema-registry kafka-avro-console-producer \
  --topic input-topic \
  --bootstrap-server broker:29092 \
  --property schema.registry.url=http://localhost:8081 \
  --property value.schema='{"type":"record","name":"Example","fields":[{"name":"id","type":"string"}]}'

# Consume output (use schema-aware consumer)
# For other formats, use kafka-json-schema-console-consumer or kafka-protobuf-console-consumer.
docker exec schema-registry kafka-avro-console-consumer \
  --topic output-topic \
  --from-beginning \
  --bootstrap-server broker:29092 \
  --property schema.registry.url=http://localhost:8081 \
  --property print.key=true \
  --key-deserializer org.apache.kafka.common.serialization.StringDeserializer

# Stop
docker compose down
```

## Notes

- `confluentinc/confluent-local:8.2.0` uses KRaft (no ZooKeeper) and is optimized for local development
- Replication factor is set to 1 since there's only one broker
- For EOS testing, `transaction.state.log.replication.factor` must be 1 in single-broker mode
- Schema Registry is required because all data is schematized (project invariant). Never use plain `kafka-console-producer` / `kafka-console-consumer` for schematized topics — always use the schema-aware variants (`kafka-avro-console-producer`, etc.)
- The `kafka-avro-console-producer` and `kafka-avro-console-consumer` CLIs are bundled in the `schema-registry` container, so run them via `docker exec schema-registry`. Broker-only commands like `kafka-topics` run via `docker exec broker`.
- `kafka-avro-console-consumer` defaults `KafkaAvroDeserializer` for **both** key and value. Our topologies write string keys with `Serdes.String()` (no SR framing), so always pass `--key-deserializer org.apache.kafka.common.serialization.StringDeserializer` — otherwise the Avro deserializer chokes on the first byte (expects `0x00` magic + 4-byte schema ID). Same applies to `kafka-protobuf-console-consumer` and `kafka-json-schema-console-consumer`.
- `group.protocol=streams` requires broker version AK 4.2+. The `confluentinc/confluent-local:8.2.0` image bundles CP 8.2 which includes AK 4.2, so it works locally. If using an older image version (e.g., 7.x), comment out `group.protocol=streams` in your Streams config.
- For local dev, topics can use the `--if-not-exists` flag since `auto.create.topics.enable=true` by default on the local broker, but pre-creating topics with explicit partition counts is still recommended to avoid surprises.

## Why No Production Docker Compose?

This skill does not generate a docker-compose for production Kafka clusters. In production, the Kafka cluster is managed infrastructure — either Confluent Cloud (fully managed) or Confluent Platform deployed via Ansible/Terraform/Helm. The Streams *application* runs as a containerized microservice (see `references/production-hardening.md` for Dockerfile and deployment sizing), connecting to the cluster via `bootstrap.servers`. You don't run the broker and the app in the same compose file in production.
