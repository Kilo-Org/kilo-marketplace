# Verification and Operations

Checklists for verifying a Kafka Streams app, schema-aware tooling, and application reset procedures.

## Verification — agent runs this before handing off

Compiling + `TopologyTestDriver` tests passing is **not** a working app. You must run against a real broker and observe `State transition from REBALANCING to RUNNING` before handing off. Common failure modes that compile and test-pass cleanly but die at startup:

- `NoClassDefFoundError` on a Confluent class → missing runtime dep; check `build-templates.md`
- Silent log output / `Failed to load class org.slf4j.impl.StaticLoggerBinder` → SLF4J API/impl version skew
- `cannot find symbol` on a Streams API → check the import path against KS 4.x (`debugging.md` § Startup Failures)
- Auth failures → check `.env`, bootstrap URL, and SR creds

### Local (Apache Kafka / Confluent Platform via docker-compose)

You run the whole thing yourself.

1. `docker compose up -d` — start Kafka + Schema Registry. Wait for both to be healthy (`docker compose ps`, or `curl localhost:8081/subjects`).
2. `./create-topics.sh` — pre-create source, output, and DLQ topics
3. Start the app **in the background** so you can read logs while it runs: `./gradlew run > app.log 2>&1 &` (or `mvn exec:java`, or the harness's background mode)
4. Tail `app.log` and confirm `State transition from REBALANCING to RUNNING` within ~30s. If you don't, read the actual error and fix it before continuing — do **not** hand off a non-running app.
5. If sample data was requested: produce records (see [Schema-Aware Producers](#schema-aware-producers)) and confirm they land on the output topic (see [Consuming Output](#consuming-output)).
6. Check logs — no deserialization exceptions, no rebalancing loops.
7. Stop the app and `docker compose down` (or leave running if the user wants to keep iterating — ask).

State explicitly in the handoff that you observed `RUNNING` (and processed records, if step 5 ran).

### Confluent Cloud

You usually cannot run end-to-end because the cluster + SR API keys are the user's. **Do not fabricate a successful run.** Pick the branch that matches the actual situation:

**A. Real CC creds are available** (user pasted them, pointed you at a real `.env`, or you have creds for a sandbox cluster):

1. Verify `confluent` CLI auth if you'll use it: `confluent login`, then `confluent environment use <env-id>` and `confluent kafka cluster use <cluster-id>`
2. `./create-topics.sh --cloud` — pre-create topics
3. `./gradlew run` (auto-loads `.env`). Watch the log for `State transition from REBALANCING to RUNNING`. Fix any startup error before proceeding.
4. Produce test data: `./gradlew produce` if a sample producer was generated, otherwise see [Schema-Aware Producers](#schema-aware-producers).
5. Verify output — **must include SR credentials for schematized topics**:
   ```bash
   confluent kafka topic consume <output-topic> --from-beginning --print-key \
     --value-format avro \
     --schema-registry-endpoint $SCHEMA_REGISTRY_URL \
     --schema-registry-api-key $SCHEMA_REGISTRY_API_KEY \
     --schema-registry-api-secret $SCHEMA_REGISTRY_API_SECRET
   ```
   Replace `avro` with `protobuf` or `jsonschema` as appropriate.

**B. Creds are placeholders or missing:**

1. Run `./gradlew build` (compile + unit tests). Report pass/fail.
2. Hand the user the exact commands to run themselves — steps 2–5 above — and tell them what success looks like (`State transition from REBALANCING to RUNNING` in the log; records on the output topic).
3. Say plainly: "I couldn't run this against your CC cluster because I don't have your API keys — please run these steps and paste any errors back." Do not imply a runtime verification you didn't perform.

See `references/cli-commands.md` for the full CLI reference.

## Schema-Aware Producers

**Never use plain `kafka-console-producer` for schematized topics** — it produces raw strings without the Schema Registry magic byte, causing `Unknown magic byte!` deserialization errors.

### Local / Confluent Platform

```bash
# Avro
kafka-avro-console-producer --bootstrap-server localhost:9092 \
  --topic input-topic --property schema.registry.url=http://localhost:8081 \
  --property value.schema='<avro-schema>'

# Protobuf
kafka-protobuf-console-producer --bootstrap-server localhost:9092 \
  --topic input-topic --property schema.registry.url=http://localhost:8081 \
  --property value.schema='<protobuf-schema>'

# JSON Schema
kafka-json-schema-console-producer --bootstrap-server localhost:9092 \
  --topic input-topic --property schema.registry.url=http://localhost:8081 \
  --property value.schema='<json-schema>'
```

### Confluent Cloud

```bash
confluent kafka topic produce <topic> --value-format avro \
  --schema '<avro-schema-json>'
# Or with a schema file:
confluent kafka topic produce <topic> --value-format avro \
  --schema @path/to/schema.avsc
```

### Generated SampleDataProducer (recommended)

If the user wants sample data, generate a `SampleDataProducer.java` class and a separate Gradle `produce` task. This is more reliable than CLI producers for complex schemas. Run with `./gradlew produce`.

## Consuming Output

### Local / Confluent Platform

```bash
# Avro
# Keys are Serdes.String() in our topologies — override the default key
# deserializer so the consumer doesn't try to Avro-decode a raw UTF-8 key
# (which has no 0x00 magic byte + 4-byte schema ID).
kafka-avro-console-consumer --bootstrap-server broker:29092 \
  --topic output-topic --from-beginning \
  --property schema.registry.url=http://localhost:8081 \
  --property print.key=true \
  --key-deserializer org.apache.kafka.common.serialization.StringDeserializer
```

### Confluent Cloud

```bash
# IMPORTANT: Include SR credentials — without them, Avro/Protobuf/JSON Schema
# data is displayed as raw bytes (unreadable)
confluent kafka topic consume output-topic --from-beginning --print-key \
  --value-format avro \
  --schema-registry-endpoint <SR_URL> \
  --schema-registry-api-key <SR_KEY> \
  --schema-registry-api-secret <SR_SECRET>
```

## Resetting Application State

During development, schema changes or bad data can corrupt internal state. Use this procedure to fully reset.

### Prerequisites

The `kafka-streams-application-reset` tool ships with Apache Kafka.

If you don't have it:
- **Apache Kafka:** Download from https://kafka.apache.org/downloads — tool is at `bin/kafka-streams-application-reset.sh`
- **Confluent Platform:** Tool is at `$CONFLUENT_HOME/bin/kafka-streams-application-reset`
- **Confluent Cloud users:** You still need the Apache Kafka download for this tool. It connects to your CC cluster using a `client.properties` file.

### Reset Steps

1. **Stop all instances of the application**

2. **Reset consumer offsets and internal topics:**

   **Local (no auth):**
   ```bash
   kafka-streams-application-reset \
     --application-id <app-id> \
     --bootstrap-server localhost:9092 \
     --input-topics <topic1>,<topic2>
   ```

   **Confluent Cloud or secured clusters:**
   ```bash
   kafka-streams-application-reset \
     --application-id <app-id> \
     --bootstrap-server <bootstrap-servers> \
     --input-topics <topic1>,<topic2> \
     --command-config client.properties
   ```

   Create `client.properties` for CC:
   ```properties
   security.protocol=SASL_SSL
   sasl.mechanism=PLAIN
   sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required \
     username='<CLUSTER_API_KEY>' password='<CLUSTER_API_SECRET>';
   ```

3. **Delete stale schemas** on changelog/repartition subjects if you changed your POJOs:
   ```bash
   # List subjects
   curl -u <SR_KEY>:<SR_SECRET> <SR_URL>/subjects | grep <app-id>
   # Soft + hard delete each stale subject
   curl -X DELETE -u <SR_KEY>:<SR_SECRET> <SR_URL>/subjects/<subject>?permanent=false
   curl -X DELETE -u <SR_KEY>:<SR_SECRET> <SR_URL>/subjects/<subject>?permanent=true
   ```

4. **Clean up local state stores:**
   ```bash
   # Default location:
   rm -rf /tmp/kafka-streams/<application-id>
   # Or whatever state.dir is configured to in application.properties
   ```
   - **Multi-node deployments (K8s, ECS, etc.):** Clean local state from each node. For K8s StatefulSets, clear the PVC on each pod or redeploy with a fresh `application.id`.

5. **Restart the application** — it will re-process from the beginning

### When to Reset

- Schema changes to POJOs used in state stores (causes deserialization errors on changelog replay)
- Corrupt state from bad test data
- Switching between `json.value.type` configurations
- After deleting and recreating topics (stale schema ID references)

### Alternative: Fresh application.id

Instead of a full reset, you can change `application.id` (e.g., `my-app-v2` -> `my-app-v3`). This creates entirely new consumer groups and internal topics, bypassing any state corruption. The old internal topics become orphaned and should be cleaned up later.

### Full Teardown

For demos or development, use the generated `teardown.sh` script to delete all topics, internal topics, and local state in one command. See `scripts/teardown.sh` for the template.

Include this reset procedure in the generated README for all stateful apps.
