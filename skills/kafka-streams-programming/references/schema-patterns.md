# Schema Patterns

Correct schema examples for Avro, Protobuf, and JSON Schema. Follow these exactly — incorrect patterns cause subtle build and runtime failures.

## Avro

### Schema file location

**Gradle Avro plugin expects schemas in `src/main/avro/`**, NOT `src/main/resources/avro/`.

```
src/main/avro/
├── MyInput.avsc
└── MyOutput.avsc
```

If schemas are in `src/main/resources/avro/`, the Gradle Avro plugin will report `NO-SOURCE` and skip code generation. The build succeeds but no Java classes are generated, causing compilation errors downstream.

### Logical types — CORRECT nesting

Avro logical types MUST be nested inside the `type` field as a type definition object. This is the most common mistake.

**CORRECT:**
```json
{
  "name": "timestamp",
  "type": {"type": "long", "logicalType": "timestamp-millis"}
}
```

**WRONG — DO NOT DO THIS:**
```json
{
  "name": "timestamp",
  "type": "long",
  "logicalType": "timestamp-millis"
}
```

The wrong form causes the Avro plugin to silently ignore the logical type, or (with newer Avro versions) generate `Instant` fields instead of `long`, breaking compilation in topology code that expects `long`.

### All logical type examples

```json
// timestamp-millis (milliseconds since epoch)
{"name": "created_at", "type": {"type": "long", "logicalType": "timestamp-millis"}}

// timestamp-micros (microseconds since epoch)
{"name": "precise_ts", "type": {"type": "long", "logicalType": "timestamp-micros"}}

// date (days since epoch)
{"name": "birth_date", "type": {"type": "int", "logicalType": "date"}}

// time-millis (milliseconds since midnight)
{"name": "start_time", "type": {"type": "int", "logicalType": "time-millis"}}

// decimal (fixed-point)
{"name": "amount", "type": {"type": "bytes", "logicalType": "decimal", "precision": 10, "scale": 2}}

// uuid
{"name": "id", "type": {"type": "string", "logicalType": "uuid"}}
```

### Nullable logical types

```json
{"name": "deleted_at", "type": ["null", {"type": "long", "logicalType": "timestamp-millis"}], "default": null}
```

### Java type mapping with logical types

When the Avro plugin generates code with logical types enabled (default in recent versions):

| Avro logicalType | Generated Java type | Use in code |
|---|---|---|
| `timestamp-millis` | `java.time.Instant` | `Instant.now()`, `Instant.EPOCH` |
| `timestamp-micros` | `java.time.Instant` | Same as above |
| `date` | `java.time.LocalDate` | `LocalDate.now()` |
| `time-millis` | `java.time.LocalTime` | `LocalTime.now()` |
| `decimal` | `java.math.BigDecimal` | `BigDecimal.ZERO` |
| `uuid` | `java.util.UUID` | `UUID.randomUUID()` |

**CRITICAL — common compilation errors with logical types:**

Avro 1.12+ with the Gradle Avro plugin generates `Instant` (not `long`) for `timestamp-millis`. All code touching these fields must use `java.time.Instant`. This affects topology aggregations, initializers, producers, and tests.

**WRONG — causes `incompatible types: long cannot be converted to Instant`:**
```java
// Aggregation initializer
stats.setLastOrderTime(0L);                              // WRONG
// Timestamp comparison
updated.setTimestamp(Math.max(a.getTimestamp(), b.getTimestamp())); // WRONG — Math.max doesn't accept Instant
// Producer
order.setTimestamp(Instant.now().toEpochMilli());          // WRONG — toEpochMilli() returns long
// Test helper
event.setTimestamp(1000L);                                 // WRONG
```

**CORRECT:**
```java
// Aggregation initializer
stats.setLastOrderTime(Instant.EPOCH);
// Timestamp comparison
updated.setTimestamp(a.getTimestamp().isAfter(b.getTimestamp()) ? a.getTimestamp() : b.getTimestamp());
// Producer
order.setTimestamp(Instant.now());
// Test helper
event.setTimestamp(Instant.ofEpochMilli(1000L));
```

Same pattern applies to all logical types: use `LocalDate` not `int` for `date`, `BigDecimal` not `bytes` for `decimal`, etc.

### Schema evolution defaults

When generating Avro schemas, follow these rules for schema evolution compatibility:

- ALL optional fields should have defaults
- Use sensible defaults: `""` for strings, `0` for numbers, `false` for booleans, `null` for nullable unions
- Enums should have a `default` value (the first symbol) for forward compatibility

**Example with proper defaults:**
```json
{
  "type": "record",
  "name": "Transaction",
  "namespace": "com.example",
  "fields": [
    {"name": "account_id", "type": "string"},
    {"name": "amount", "type": "double", "default": 0.0},
    {"name": "type", "type": {"type": "enum", "name": "TxnType",
      "symbols": ["CREDIT", "DEBIT"], "default": "CREDIT"}},
    {"name": "timestamp", "type": {"type": "long",
      "logicalType": "timestamp-millis"}, "default": 0}
  ]
}
```

**Example output schema (consumed by downstream):**
```json
{
  "type": "record",
  "name": "AccountSummary",
  "namespace": "com.example",
  "fields": [
    {"name": "account_id", "type": "string"},
    {"name": "total_credits", "type": "double", "default": 0.0},
    {"name": "total_debits", "type": "double", "default": 0.0},
    {"name": "balance", "type": "double", "default": 0.0},
    {"name": "transaction_count", "type": "long", "default": 0},
    {"name": "last_updated", "type": {"type": "long",
      "logicalType": "timestamp-millis"}, "default": 0}
  ]
}
```

For output schemas consumed by downstream apps: always use BACKWARD compatibility (new schema can read old data). This is the Schema Registry default.

## Protobuf

### Schema file location

```
src/main/proto/
├── my_input.proto
└── my_output.proto
```

### Gradle plugin requirement

The `com.google.protobuf` Gradle plugin is **required** to compile `.proto` files into Java classes. Without it, proto files sit uncompiled and your topology code fails with missing class errors — the same failure mode as the Avro directory bug.

```groovy
plugins {
    id 'com.google.protobuf' version '0.9.4'
}

protobuf {
    protoc {
        artifact = 'com.google.protobuf:protoc:4.31.1'
    }
}

dependencies {
    implementation 'io.confluent:kafka-streams-protobuf-serde:8.2.0'
    implementation 'com.google.protobuf:protobuf-java:4.31.1'
}
```

See `references/build-templates.md` for the complete Protobuf build.gradle.

### Example

```protobuf
syntax = "proto3";
package com.example;

option java_package = "com.example.proto";
option java_outer_classname = "TransactionProtos";

import "google/protobuf/timestamp.proto";

message Transaction {
  string account_id = 1;
  double amount = 2;
  TxnType type = 3;
  google.protobuf.Timestamp timestamp = 4;
}

enum TxnType {
  CREDIT = 0;
  DEBIT = 1;
}
```

Use `option java_package` and `option java_outer_classname` to control the generated Java class location and name.

### Protobuf timestamps

Use `google.protobuf.Timestamp` — it handles seconds + nanos. Import `google/protobuf/timestamp.proto`.

In Java code, create timestamps with:
```java
import com.google.protobuf.Timestamp;
Timestamp ts = Timestamp.newBuilder()
    .setSeconds(System.currentTimeMillis() / 1000)
    .setNanos(0)
    .build();
```

### Protobuf serde configuration

For the `KafkaProtobufSerde` default value serde, the deserializer returns `DynamicMessage` by default. To get typed messages, set `specific.protobuf.value.type`:

```java
Map<String, Object> serdeConfig = new HashMap<>();
serdeConfig.put("schema.registry.url", srUrl);
serdeConfig.put("specific.protobuf.value.type", Transaction.class.getName());
KafkaProtobufSerde<Transaction> serde = new KafkaProtobufSerde<>();
serde.configure(serdeConfig, false);
```

This is analogous to JSON Schema's `json.value.type` — without it, you get `DynamicMessage` instead of your generated class.

### Protobuf schema evolution

Proto3 fields are optional by default and have zero-value defaults (0 for numbers, "" for strings, false for booleans). New fields added with new field numbers are backward compatible. Never reuse field numbers — mark removed fields as `reserved`.

## JSON Schema

### Schema file location

JSON Schema does not use code generation. Define POJOs manually with Jackson annotations.

```
src/main/java/com/example/<appname>/model/
├── Transaction.java
└── AccountSummary.java
```

See `references/build-templates.md` for the JSON Schema build.gradle (no schema plugin needed, add `jackson-databind` dependency).

### Example POJO

POJOs need: (1) a no-arg constructor (Jackson requirement), (2) getters and setters, (3) `@JsonProperty` for names that differ from Java convention.

```java
import com.fasterxml.jackson.annotation.JsonProperty;

public class Transaction {
    @JsonProperty("account_id")
    private String accountId;
    private double amount;
    private String type;
    private long timestamp;

    // No-arg constructor REQUIRED for Jackson deserialization
    // Without it, you get: "Cannot construct instance of Transaction (no Creators)"
    public Transaction() {}

    public Transaction(String accountId, double amount, String type, long timestamp) {
        this.accountId = accountId;
        this.amount = amount;
        this.type = type;
        this.timestamp = timestamp;
    }

    public String getAccountId() { return accountId; }
    public void setAccountId(String accountId) { this.accountId = accountId; }
    public double getAmount() { return amount; }
    public void setAmount(double amount) { this.amount = amount; }
    public String getType() { return type; }
    public void setType(String type) { this.type = type; }
    public long getTimestamp() { return timestamp; }
    public void setTimestamp(long timestamp) { this.timestamp = timestamp; }
}
```

### Critical: always set json.value.type

Without `json.value.type`, the serde deserializes to `LinkedHashMap` instead of your POJO, causing `ClassCastException` at runtime.

This affects BOTH explicit serde instances AND the default value serde:

```java
// Per-serde instance (explicit)
Map<String, Object> serdeConfig = new HashMap<>(baseConfig);
serdeConfig.put("json.value.type", Transaction.class.getName());
KafkaJsonSchemaSerde<Transaction> serde = new KafkaJsonSchemaSerde<>();
serde.configure(serdeConfig, false);
```

**Default value serde gotcha:** When you set `default.value.serde=KafkaJsonSchemaSerde`, internal topics (changelog, repartition) use it. But `json.value.type` can only be set to one class globally. If your topology has multiple value types (input: Transaction, output: AccountSummary), the default can only handle one.

Solution: set the default to the type used in state stores (the aggregation output), and use explicit serdes for everything else:

```java
// In application.properties:
// default.value.serde=io.confluent.kafka.streams.serdes.json.KafkaJsonSchemaSerde
// json.value.type=com.example.model.AccountSummary  <-- changelog type

// In TopologyBuilder: explicit serde for input
KafkaJsonSchemaSerde<Transaction> txnSerde = new KafkaJsonSchemaSerde<>();
txnSerde.configure(Map.of(
    "schema.registry.url", srUrl,
    "json.value.type", Transaction.class.getName()
), false);

KStream<String, Transaction> input = builder.stream(
    "transactions",
    Consumed.with(Serdes.String(), txnSerde));
```
