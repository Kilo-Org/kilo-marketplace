# Detection Patterns Reference

Patterns for detecting Kafka applications, dependencies, producers, consumers, and serializers.

## Build Files & Dependencies

### Glob Patterns
```
**/pom.xml
**/build.gradle
**/build.gradle.kts
**/requirements.txt
**/pyproject.toml
**/setup.py
**/setup.cfg
**/Pipfile
**/*.csproj
**/packages.config
**/Directory.Packages.props
**/go.mod
**/package.json
```

### Dependency Detection

| Language | Dependency Strings |
|----------|-------------------|
| Java | `spring-kafka`, `kafka-clients`, `kafka-streams`, `spring-cloud-stream`, `io.confluent`, `confluent-kafka` |
| Python | `confluent-kafka`, `confluent_kafka`, `kafka-python`, `faust-streaming`, `faust` |
| .NET | `Confluent.Kafka`, `Confluent.SchemaRegistry`, `Confluent.SchemaRegistry.Serdes` |
| Go | `confluent-kafka-go`, `github.com/Shopify/sarama`, `github.com/IBM/sarama`, `github.com/segmentio/kafka-go` |
| Node/TS | `kafkajs`, `node-rdkafka`, `@confluentinc/kafka-javascript`, `kafka-node` |

## Producer Detection

| Language | Patterns |
|----------|----------|
| Java | `KafkaTemplate`, `KafkaProducer`, `ProducerRecord`, `@SendTo`, `StreamBridge`, `ProducerFactory`, `KStream`, `KTable`, `StreamsBuilder`, `.to(`, `.through(` |
| Python | `Producer(`, `SerializingProducer(`, `AvroProducer(`, `.produce(`, `send(topic` |
| .NET | `ProducerBuilder`, `IProducer`, `ProduceAsync`, `.Produce(` |
| Go | `kafka.NewProducer`, `sarama.NewSyncProducer`, `sarama.NewAsyncProducer`, `kafka.NewWriter` |
| Node/TS | `producer.send(`, `kafka.producer(`, `producer.produce(`, `.sendBatch(` |

## Consumer Detection

| Language | Patterns |
|----------|----------|
| Java | `@KafkaListener`, `KafkaConsumer`, `ConsumerRecords`, `KafkaMessageListenerContainer`, `ConcurrentMessageListenerContainer` |
| Python | `Consumer(`, `DeserializingConsumer(`, `AvroConsumer(`, `.subscribe(`, `.poll(` |
| .NET | `ConsumerBuilder`, `IConsumer`, `.Consume(`, `ConsumerConfig` |
| Go | `kafka.NewConsumer`, `sarama.NewConsumerGroup`, `kafka.NewReader`, `.ReadMessage(` |
| Node/TS | `consumer.run(`, `kafka.consumer(`, `consumer.subscribe(`, `eachMessage` |

## Serializer Detection

### Grep Patterns
```
key.serializer
value.serializer
key.deserializer
value.deserializer
KafkaAvroSerializer
KafkaJsonSchemaSerializer
KafkaProtobufSerializer
StringSerializer
ByteArraySerializer
JsonSerializer
AvroSerializer
ProtobufSerializer
HeaderSchemaIdSerializer
schema.registry.url
SchemaRegistryClient
CachedSchemaRegistryClient
```

### Serializer Classification

| Serializer Found | Schema Format | SR Integrated? |
|-----------------|---------------|----------------|
| `KafkaAvroSerializer` / `AvroSerializer` | AVRO | Yes |
| `KafkaJsonSchemaSerializer` / `JsonSchemaSerializer` | JSON | Yes |
| `KafkaProtobufSerializer` / `ProtobufSerializer` | PROTOBUF | Yes |
| `StringSerializer` + JSON data in code | JSON (infer) | No — flag for upgrade |
| `ByteArraySerializer` + Avro in code | AVRO (infer) | No — flag for upgrade |
| `JsonSerializer` (Spring default) | JSON (infer) | No — flag for upgrade |
| Custom serializer | Infer from code | No — flag for upgrade |
| No serializer / raw produce | JSON (infer) | No — flag for upgrade |

## Custom Serializer Detection

### Java
```
implements Serializer<
implements Serializer\b
extends Serializer<
class.*Serializer.*implements
org.apache.kafka.common.serialization.Serializer
```

Look for classes that:
- Implement `org.apache.kafka.common.serialization.Serializer<T>`
- Contain `serialize(String topic,` method
- Use `ObjectMapper`, `Gson`, `Jackson`, `org.json`, or manual JSON construction → JSON format
- Use `GenericDatumWriter`, `SpecificDatumWriter`, `BinaryEncoder` → AVRO format
- Use `com.google.protobuf`, `toByteArray()` → PROTOBUF format
- Do NOT reference `schema.registry.url` or `SchemaRegistryClient`

### Python
```
def serializer(
def serialize(
def value_serializer(
json.dumps.*produce
json.dumps.*send
msgpack.pack
pickle.dumps
fastavro
avro.io
DatumWriter
BinaryEncoder
```

Format determination:
- `json.dumps()` → JSON Schema (`.json`)
- `fastavro` or `avro.io` → Avro (`.avsc`)
- `protobuf` → Protobuf (`.proto`)

### .NET
```
ISerializer<
IAsyncSerializer<
class.*:.*ISerializer
class.*:.*IAsyncSerializer
JsonConvert.SerializeObject
System.Text.Json.JsonSerializer.Serialize
Avro.IO
Avro.Specific
Avro.Generic
Google.Protobuf
```

### Go
```
json.Marshal
json.NewEncoder
encoding/json
proto.Marshal
goavro
avro.Marshal
avro.NewCodec
```

### Node/TS
```
JSON.stringify.*send
JSON.stringify.*produce
Buffer.from.*JSON
serialize.*value
```

## Risk Detection

### auto.register.schemas=true
```
auto.register.schemas\s*=\s*true
auto\.register\.schemas.*true
AutoRegisterSchemas\s*=\s*true
auto_register_schemas.*True
autoRegisterSchemas.*true
```

**Files to prioritize:**
```
**/*.properties
**/*.yml
**/*.yaml
**/application*.properties
**/application*.yml
**/*.java
**/*.py
**/*.cs
**/*.go
**/*.ts
**/*.js
**/*.json
```

### use.latest.version
```
use.latest.version\s*=\s*true
use\.latest\.version.*true
UseLatestVersion\s*=\s*true
```
