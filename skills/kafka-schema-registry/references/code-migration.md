# Code Migration Reference

This reference provides serializer and deserializer implementation patterns for migrating existing Kafka applications to use Confluent Schema Registry with Avro, Protobuf, or JSON Schema serialization.

## When to Use

After generating the schema analysis report, use this reference when users want to:
- Update their producer/consumer code to use Schema Registry
- Migrate from string/JSON/custom serializers to Schema Registry-managed formats
- Implement proper serialization/deserialization with Avro, Protobuf, or JSON Schema
- Choose the appropriate schema format for their use case

## Choosing a Schema Format

If the user hasn't specified their desired schema format, ask if they would like to use Avro, Protobuf, or JSON Schema. The following guidance can help their decision:

| Format | Best For | Pros | Cons |
|--------|----------|------|------|
| **Avro** | High-throughput data pipelines, analytics | Compact binary format, rich schema evolution, fast serialization | Requires code generation, less human-readable |
| **Protobuf** | Microservices, gRPC integration, cross-language | Compact, widely adopted, strong typing, backward/forward compatible | Requires code generation, steeper learning curve |
| **JSON Schema** | Web APIs, gradual migration from JSON, human readability | Human-readable, no code generation, familiar to web devs | Larger payload size, slower serialization |

**Recommendation:** Use Avro for data-intensive pipelines, Protobuf for service-to-service communication, JSON Schema for gradual migrations from plain JSON.

## Migration Workflow

1. Review the schema report to identify applications needing migration
2. For each application, determine the language and role (producer/consumer)
3. Choose the appropriate schema format (Avro, Protobuf, or JSON Schema)
4. Update dependencies to include Schema Registry client libraries
5. Replace existing serializers/deserializers with Schema Registry-aware versions
6. Update configuration to include Schema Registry connection details
7. Test with the schemas generated in the `schemas/` directory

---

## Python

### Dependencies

```python
# requirements.txt or pyproject.toml

# For Avro:
confluent-kafka[avro]

# For Protobuf:
confluent-kafka[protobuf]

# For JSON Schema:
confluent-kafka[json]


### Avro

#### Producer Pattern

```python
from confluent_kafka.schema_registry.avro import AvroSerializer

avro_serializer = AvroSerializer(schema_registry_client, schema_string, value_to_dict)

producer.produce(
    topic=topic,
    value=avro_serializer(value_obj, SerializationContext(topic, MessageField.VALUE))
)
```

#### Consumer Pattern

```python
from confluent_kafka.schema_registry.avro import AvroDeserializer

avro_deserializer = AvroDeserializer(schema_registry_client, schema_str, dict_to_value)

msg = consumer.poll(1.0)
value_obj = avro_deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))
```

### Protobuf

#### Producer Pattern

```python
from confluent_kafka.schema_registry.protobuf import ProtobufSerializer

# Create serializer
protobuf_serializer = ProtobufSerializer(
    YourMessage,  # Protobuf message class
    schema_registry_client,
    {'use.latest.version': True}
)

producer.produce(
    topic=topic,
    value=protobuf_serializer(value_obj, SerializationContext(topic, MessageField.VALUE))
)
```

#### Consumer Pattern

```python
from confluent_kafka.schema_registry.protobuf import ProtobufDeserializer

protobuf_deserializer = ProtobufDeserializer(
    YourMessage,
    {'use.deprecated.format': False}
)

msg = consumer.poll(1.0)
value_obj = protobuf_deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))
```

### JSON Schema

#### Producer Pattern

```python
from confluent_kafka.schema_registry.json_schema import JSONSerializer

json_serializer = JSONSerializer(schema_str, schema_registry_client, value_to_dict)

producer.produce(
    topic=topic,
    value=json_serializer(value_obj, SerializationContext(topic, MessageField.VALUE))
)
```

#### Consumer Pattern

```python
from confluent_kafka.schema_registry.json_schema import JSONDeserializer

json_deserializer = JSONDeserializer(schema_str, dict_to_value)

msg = consumer.poll(1.0)
value_obj = json_deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))
```

---

## Java

### Dependencies

```xml
<!-- Maven pom.xml -->

<!-- For Avro: -->
<dependency>
    <groupId>io.confluent</groupId>
    <artifactId>kafka-avro-serializer</artifactId>
</dependency>

<!-- For Protobuf: -->
<dependency>
    <groupId>io.confluent</groupId>
    <artifactId>kafka-protobuf-serializer</artifactId>
</dependency>

<!-- For JSON Schema: -->
<dependency>
    <groupId>io.confluent</groupId>
    <artifactId>kafka-json-schema-serializer</artifactId>
</dependency>
```

```gradle
// Gradle build.gradle

// For Avro:
implementation 'io.confluent:kafka-avro-serializer'

// For Protobuf:
implementation 'io.confluent:kafka-protobuf-serializer'

// For JSON Schema:
implementation 'io.confluent:kafka-json-schema-serializer'
```

### Avro

#### Producer Pattern

```java
import io.confluent.kafka.serializers.KafkaAvroSerializer;

// Set serializer in producer properties
props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, KafkaAvroSerializer.class.getName());

KafkaProducer<String, YourAvroModel> producer = new KafkaProducer<>(props);

// YourAvroModel is a generated Avro class
YourAvroModel value = new YourAvroModel(...);
producer.send(new ProducerRecord<>(topic, key, value));
```

#### Consumer Pattern

```java
import io.confluent.kafka.serializers.KafkaAvroDeserializer;
import io.confluent.kafka.serializers.KafkaAvroDeserializerConfig;

// Set deserializer in consumer properties
props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, KafkaAvroDeserializer.class.getName());

Consumer<String, YourAvroModel> consumer = new KafkaConsumer<>(props);

while (true) {
    ConsumerRecords<String, YourAvroModel> records = consumer.poll(Duration.ofMillis(100));
    for (ConsumerRecord<String, YourAvroModel> record : records) {
        YourAvroModel value = record.value();
        // Process value
    }
}
```

### Protobuf

#### Producer Pattern

```java
import io.confluent.kafka.serializers.protobuf.KafkaProtobufSerializer;

// Set serializer in producer properties
props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, KafkaProtobufSerializer.class.getName());

KafkaProducer<String, YourProtoModel> producer = new KafkaProducer<>(props);

// YourProtoModel is a generated Protobuf class
YourProtoModel value = YourProtoModel.newBuilder()
    .setField1("value1")
    .setField2(123)
    .build();

producer.send(new ProducerRecord<>(topic, key, value));
```

#### Consumer Pattern

```java
import io.confluent.kafka.serializers.protobuf.KafkaProtobufDeserializer;
import io.confluent.kafka.serializers.protobuf.KafkaProtobufDeserializerConfig;

// Set deserializer in consumer properties
props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, KafkaProtobufDeserializer.class.getName());
props.put(KafkaProtobufDeserializerConfig.SPECIFIC_PROTOBUF_VALUE_TYPE, YourProtoModel.class.getName());

Consumer<String, YourProtoModel> consumer = new KafkaConsumer<>(props);

while (true) {
    ConsumerRecords<String, YourProtoModel> records = consumer.poll(Duration.ofMillis(100));
    for (ConsumerRecord<String, YourProtoModel> record : records) {
        YourProtoModel value = record.value();
        // Process value
    }
}
```

### JSON Schema

#### Producer Pattern

```java
import io.confluent.kafka.serializers.json.KafkaJsonSchemaSerializer;

// Set serializer in producer properties
props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, KafkaJsonSchemaSerializer.class.getName());

KafkaProducer<String, YourPOJO> producer = new KafkaProducer<>(props);

// YourPOJO is a Java class with Jackson annotations
YourPOJO value = new YourPOJO("value1", 123);
producer.send(new ProducerRecord<>(topic, key, value));
```

#### Consumer Pattern

```java
import io.confluent.kafka.serializers.json.KafkaJsonSchemaDeserializer;
import io.confluent.kafka.serializers.json.KafkaJsonSchemaDeserializerConfig;

// Set deserializer in consumer properties
props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, KafkaJsonSchemaDeserializer.class.getName());
props.put(KafkaJsonSchemaDeserializerConfig.JSON_VALUE_TYPE, YourPOJO.class.getName());

Consumer<String, YourPOJO> consumer = new KafkaConsumer<>(props);

while (true) {
    ConsumerRecords<String, YourPOJO> records = consumer.poll(Duration.ofMillis(100));
    for (ConsumerRecord<String, YourPOJO> record : records) {
        YourPOJO value = record.value();
        // Process value
    }
}
```

---

## JavaScript/Node.js

### Dependencies

```json
{
  "dependencies": {
    "@confluentinc/kafka-javascript": "1.9.1",
    "@confluentinc/schemaregistry": "1.9.1",
    "protobufjs": "8.6.5"
  }
}
```

**Note:** The `@confluentinc/schemaregistry` package supports Avro, Protobuf, and JSON Schema serialization.

### Avro

#### Producer Pattern

```javascript
const {
  SchemaRegistryClient,
  SerdeType,
  AvroSerializer
} = require("@confluentinc/schemaregistry");

// Create serializer
const serializer = new AvroSerializer(srClient, SerdeType.VALUE, {
  useLatestVersion: true
});

// Serialize value
const message = {
  value: await serializer.serialize("your-topic", { field1: "value1", field2: 123 })
};
```

#### Consumer Pattern

```javascript
const {
  SerdeType,
  AvroDeserializer
} = require("@confluentinc/schemaregistry");

const deserializer = new AvroDeserializer(srClient, SerdeType.VALUE, {});

consumer.run({
  eachMessage: async ({ topic, message }) => {
    const decodedValue = await deserializer.deserialize(topic, message.value);
    // Process decodedValue
  }
});
```

### Protobuf

#### Producer Pattern

```javascript
const {
  SerdeType,
  ProtobufSerializer
} = require("@confluentinc/schemaregistry");

// Create serializer
const serializer = new ProtobufSerializer(srClient, SerdeType.VALUE, {
  useLatestVersion: true
});

// Serialize value
const message = {
  value: await serializer.serialize("your-topic", { field1: "value1", field2: 123 })
};

await producer.send({ topic: "your-topic", messages: [message] });
```

#### Consumer Pattern

```javascript
const {
  SerdeType,
  ProtobufDeserializer
} = require("@confluentinc/schemaregistry");

const deserializer = new ProtobufDeserializer(srClient, SerdeType.VALUE, {});

consumer.run({
  eachMessage: async ({ topic, message }) => {
    const decodedValue = await deserializer.deserialize(topic, message.value);
    // Process decodedValue
  }
});
```

### JSON Schema

#### Producer Pattern

```javascript
const {
  SerdeType,
  JsonSerializer
} = require("@confluentinc/schemaregistry");

// Create serializer
const serializer = new JsonSerializer(srClient, SerdeType.VALUE, {
  useLatestVersion: true
});

// Serialize value
const message = {
  value: await serializer.serialize("your-topic", { field1: "value1", field2: 123 })
};

await producer.send({ topic: "your-topic", messages: [message] });
```

#### Consumer Pattern

```javascript
const {
  SerdeType,
  JsonDeserializer
} = require("@confluentinc/schemaregistry");

const deserializer = new JsonDeserializer(srClient, SerdeType.VALUE, {});

consumer.run({
  eachMessage: async ({ topic, message }) => {
    const decodedValue = await deserializer.deserialize(topic, message.value);
    // Process decodedValue
  }
});
```

---

## Go

### Dependencies

```go
require (
    github.com/confluentinc/confluent-kafka-go/v2
)
```

**Note:** The confluent-kafka-go package includes support for Avro, Protobuf, and JSON Schema through different serde packages.

### Avro

#### Producer Pattern

```go
import (
    "github.com/confluentinc/confluent-kafka-go/v2/schemaregistry"
    "github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/serde"
    "github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/serde/avrov2"
)

// Create Avro serializer
ser, _ := avrov2.NewSerializer(client, serde.ValueSerde, avrov2.NewSerializerConfig())

// Serialize value
value := YourStruct{Field1: "value1", Field2: 123}
payload, _ := ser.Serialize(topic, &value)

// Produce
producer.Produce(&kafka.Message{
    TopicPartition: kafka.TopicPartition{Topic: &topic, Partition: kafka.PartitionAny},
    Value:          payload,
}, deliveryChan)
```

#### Consumer Pattern

```go
import (
    "github.com/confluentinc/confluent-kafka-go/v2/schemaregistry"
    "github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/serde"
    "github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/serde/avrov2"
)

// Create Avro deserializer
deser, _ := avrov2.NewDeserializer(client, serde.ValueSerde, avrov2.NewDeserializerConfig())

// Deserialize
switch e := event.(type) {
case *kafka.Message:
    value := YourStruct{}
    deser.DeserializeInto(*e.TopicPartition.Topic, e.Value, &value)
    // Process value
}
```

### Protobuf

#### Producer Pattern

```go
import (
    "github.com/confluentinc/confluent-kafka-go/v2/schemaregistry"
    "github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/serde"
    "github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/serde/protobuf"
)

// Create Protobuf serializer
ser, _ := protobuf.NewSerializer(client, serde.ValueSerde, protobuf.NewSerializerConfig())

// Serialize value (YourProtoMessage is generated from .proto file)
value := &YourProtoMessage{Field1: "value1", Field2: 123}
payload, _ := ser.Serialize(topic, value)

// Produce
producer.Produce(&kafka.Message{
    TopicPartition: kafka.TopicPartition{Topic: &topic, Partition: kafka.PartitionAny},
    Value:          payload,
}, deliveryChan)
```

#### Consumer Pattern

```go
import (
    "github.com/confluentinc/confluent-kafka-go/v2/schemaregistry"
    "github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/serde"
    "github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/serde/protobuf"
)

// Create Protobuf deserializer
deser, _ := protobuf.NewDeserializer(client, serde.ValueSerde, protobuf.NewDeserializerConfig())

// Deserialize
switch e := event.(type) {
case *kafka.Message:
    value := YourProtoMessage{}
    deser.DeserializeInto(*e.TopicPartition.Topic, e.Value, &value)
    // Process value
}
```

### JSON Schema

#### Producer Pattern

```go
import (
    "github.com/confluentinc/confluent-kafka-go/v2/schemaregistry"
    "github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/serde"
    "github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/serde/jsonschema"
)

// Create JSON Schema serializer
ser, _ := jsonschema.NewSerializer(client, serde.ValueSerde, jsonschema.NewSerializerConfig())

// Serialize value
value := YourStruct{Field1: "value1", Field2: 123}
payload, _ := ser.Serialize(topic, &value)

// Produce
producer.Produce(&kafka.Message{
    TopicPartition: kafka.TopicPartition{Topic: &topic, Partition: kafka.PartitionAny},
    Value:          payload,
}, deliveryChan)
```

#### Consumer Pattern

```go
import (
    "github.com/confluentinc/confluent-kafka-go/v2/schemaregistry"
    "github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/serde"
    "github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/serde/jsonschema"
)

// Create JSON Schema deserializer
deser, _ := jsonschema.NewDeserializer(client, serde.ValueSerde, jsonschema.NewDeserializerConfig())

// Deserialize
switch e := event.(type) {
case *kafka.Message:
    value := YourStruct{}
    deser.DeserializeInto(*e.TopicPartition.Topic, e.Value, &value)
    // Process value
}
```
---

## .NET / C#

### Dependencies

```xml
<!-- .csproj -->

<!-- For Avro: -->
<PackageReference Include="Confluent.SchemaRegistry.Serdes.Avro" />

<!-- For Protobuf: -->
<PackageReference Include="Confluent.SchemaRegistry.Serdes.Protobuf" />

<!-- For JSON Schema: -->
<PackageReference Include="Confluent.SchemaRegistry.Serdes.Json" />
```

### Avro

#### Producer Pattern

```csharp
using Confluent.Kafka;
using Confluent.SchemaRegistry;
using Confluent.SchemaRegistry.Serdes;

using var schemaRegistry = new CachedSchemaRegistryClient(schemaRegistryConfig);
using var producer = new ProducerBuilder<string, YourAvroModel>(producerConfig)
    .SetValueSerializer(new AvroSerializer<YourAvroModel>(schemaRegistry))
    .Build();

var value = new YourAvroModel { Field1 = "value1", Field2 = 123 };
await producer.ProduceAsync(topic, new Message<string, YourAvroModel> { Key = key, Value = value });
```

#### Consumer Pattern

```csharp
using Confluent.Kafka;
using Confluent.Kafka.SyncOverAsync;
using Confluent.SchemaRegistry;
using Confluent.SchemaRegistry.Serdes;

using var schemaRegistry = new CachedSchemaRegistryClient(schemaRegistryConfig);
using var consumer = new ConsumerBuilder<string, YourAvroModel>(consumerConfig)
    .SetValueDeserializer(new AvroDeserializer<YourAvroModel>(schemaRegistry).AsSyncOverAsync())
    .Build();

consumer.Subscribe("your-topic");

while (true)
{
    var consumeResult = consumer.Consume();
    var value = consumeResult.Message.Value;
    // Process value
}
```

### Protobuf

#### Producer Pattern

```csharp
using Confluent.Kafka;
using Confluent.SchemaRegistry;
using Confluent.SchemaRegistry.Serdes;

using var schemaRegistry = new CachedSchemaRegistryClient(schemaRegistryConfig);
using var producer = new ProducerBuilder<string, YourProtoMessage>(producerConfig)
    .SetValueSerializer(new ProtobufSerializer<YourProtoMessage>(schemaRegistry))
    .Build();

var value = new YourProtoMessage { Field1 = "value1", Field2 = 123 };
await producer.ProduceAsync(topic, new Message<string, YourProtoMessage> { Key = key, Value = value });
```

#### Consumer Pattern

```csharp
using Confluent.Kafka;
using Confluent.Kafka.SyncOverAsync;
using Confluent.SchemaRegistry;
using Confluent.SchemaRegistry.Serdes;

using var schemaRegistry = new CachedSchemaRegistryClient(schemaRegistryConfig);
using var consumer = new ConsumerBuilder<string, YourProtoMessage>(consumerConfig)
    .SetValueDeserializer(new ProtobufDeserializer<YourProtoMessage>().AsSyncOverAsync())
    .Build();

consumer.Subscribe("your-topic");

while (true)
{
    var consumeResult = consumer.Consume();
    var value = consumeResult.Message.Value;
    // Process value
}
```

### JSON Schema

#### Producer Pattern

```csharp
using Confluent.Kafka;
using Confluent.SchemaRegistry;
using Confluent.SchemaRegistry.Serdes;

using var schemaRegistry = new CachedSchemaRegistryClient(schemaRegistryConfig);
using var producer = new ProducerBuilder<string, YourPOJO>(producerConfig)
    .SetValueSerializer(new JsonSerializer<YourPOJO>(schemaRegistry))
    .Build();

var value = new YourPOJO { Field1 = "value1", Field2 = 123 };
await producer.ProduceAsync(topic, new Message<string, YourPOJO> { Key = key, Value = value });
```

#### Consumer Pattern

```csharp
using Confluent.Kafka;
using Confluent.Kafka.SyncOverAsync;
using Confluent.SchemaRegistry;
using Confluent.SchemaRegistry.Serdes;

using var schemaRegistry = new CachedSchemaRegistryClient(schemaRegistryConfig);
using var consumer = new ConsumerBuilder<string, YourPOJO>(consumerConfig)
    .SetValueDeserializer(new JsonDeserializer<YourPOJO>().AsSyncOverAsync())
    .Build();

consumer.Subscribe("your-topic");

while (true)
{
    var consumeResult = consumer.Consume();
    var value = consumeResult.Message.Value;
    // Process value
}
```

---

## Migration Testing Checklist

Before deploying migrated code:

- [ ] Verify schema files in `schemas/` directory match data models
- [ ] Apply Terraform to register schemas in Schema Registry
- [ ] Test producer serialization with sample data
- [ ] Test consumer deserialization with existing topic data
- [ ] Verify PII fields are properly tagged (if applicable)
- [ ] Update CI/CD pipelines to include schema validation
- [ ] Document rollout order (consumers first for Category E, producers first for Category B)
- [ ] Plan rollback strategy (keep old serializers available initially)
- [ ] Monitor schema compatibility errors in Schema Registry
- [ ] Update monitoring/alerting for serialization failures

---

## Common Migration Issues

### Issue: Schema Mismatch
**Symptom:** Serialization/deserialization errors
**Solution:** Ensure data model matches generated schema exactly. Check field names, types, and nullability.

### Issue: Authentication Errors
**Symptom:** 401/403 errors connecting to Schema Registry
**Solution:** Verify SR API key/secret and ensure credentials have proper ACLs.

### Issue: Compatibility Errors
**Symptom:** "Schema being registered is incompatible"
**Solution:** Check Schema Registry compatibility mode. Use BACKWARD for consumers-first migration, FORWARD for producers-first.

### Issue: Performance Degradation
**Symptom:** Increased latency after migration
**Solution:** Enable schema caching. Most clients cache automatically, but verify configuration.

### Issue: Missing Schema ID in Messages
**Symptom:** Deserializer cannot find schema
**Solution:** Ensure producer is actually using AvroSerializer, not falling back to custom serializer.

---
