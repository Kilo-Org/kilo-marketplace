# Schema Inference Reference

How to extract schemas from code, data models, and inline data structures.

## Finding Existing Schemas

Search for:
```
**/*.avsc          (Avro schema)
**/*.avro          (Avro schema)
**/*.proto         (Protobuf)
**/schema*.json    (JSON Schema)
**/*.schema.json   (JSON Schema)
**/schemas/**      (schema directories)
**/avro/**         (Avro directories)
```

## Inferring from Data Models

### Java
- Classes used as generic type in `KafkaTemplate<K, V>` or `ProducerRecord<K, V>`
- Classes with `@JsonProperty`, `@JsonInclude`, Jackson annotations
- Avro-generated classes extending `SpecificRecord`
- Protobuf-generated classes extending `GeneratedMessageV3`
- Java Records used in producer calls
- POJOs with getters/setters passed to `send()`

### Python
- `@dataclass` decorated classes used in `produce()` calls
- Pydantic `BaseModel` subclasses
- `TypedDict` definitions
- Named tuples
- Dict literals passed to `produce()` — infer field types from values
- Avro schema dicts defined in code (`{"type": "record", ...}`)

### .NET
- Classes/records with `[JsonProperty]`, `[DataMember]`, or `[ProtoMember]` attributes
- Types used as generic parameter in `IProducer<TKey, TValue>`
- Classes in a `Models` or `Events` namespace near producer code

### Go
- Struct types with `json:"field_name"` tags
- Struct types used in `Produce()` calls after `json.Marshal()`
- Struct types with `avro:"field_name"` tags

### TypeScript/Node
- Interfaces or types used in `producer.send({ value: ... })`
- Zod schemas (`z.object({...})`)
- io-ts codecs
- JSON objects passed directly to send

## Inferring from Inline Data

When there's no typed class, infer from the code that constructs the data.

### Detection Patterns by Language

**Java — HashMap / Map.of / JSONObject:**
```
new HashMap<>
Map.of(
Map.ofEntries(
new JSONObject(
put("field_name",
```

**Python — dict literals:**
```
produce.*{
send.*{
json.dumps.*{
dict(
```

**Go — map[string]interface{}:**
```
map\[string\]interface
map\[string\]any
```

**Node/TS — plain objects:**
```
producer.send.*value:.*{
send.*{
```

**.NET — Dictionary / anonymous objects:**
```
new Dictionary<string
new {
anonymous
```

### Manual JSON Construction

**String concatenation/formatting:**
```java
// Java
String json = "{\"order_id\":\"" + orderId + "\",\"amount\":" + amount + "}";
String.format("{\"order_id\":\"%s\",\"amount\":%f}", orderId, amount);
```

```python
# Python
f'{{"order_id": "{order_id}", "amount": {amount}}}'
'{"order_id": "%s"}' % order_id
```

```go
// Go
fmt.Sprintf(`{"order_id":"%s","amount":%f}`, orderID, amount)
```

```javascript
// Node/TS
`{"order_id": "${orderId}", "amount": ${amount}}`
```

### JSON Tree APIs

**Java — Jackson JsonNode / ObjectNode:**
```java
ObjectNode node = mapper.createObjectNode();
node.put("order_id", orderId);
node.put("amount", amount);
```

**Java — Gson JsonObject:**
```java
JsonObject obj = new JsonObject();
obj.addProperty("order_id", orderId);
```

**.NET — JObject / JsonNode:**
```csharp
var obj = new JObject { ["order_id"] = orderId, ["amount"] = amount };
```

### Builder Patterns

```java
Event.builder().orderId(id).amount(amt).build();
new EventBuilder().setOrderId(id).setAmount(amt).build();
```

Trace the builder class to find all setter methods — each setter = field.

### Database Row / ORM Forwarding

```java
// Java — JPA/Hibernate
kafkaTemplate.send("topic", objectMapper.writeValueAsString(entity));
```

```python
# Python — SQLAlchemy / Django
producer.produce("topic", json.dumps(model.__dict__))
```

The ORM model/entity class IS the schema.

### Protobuf without SR

```java
MyEvent.newBuilder().setOrderId(id).build();
producer.send(new ProducerRecord<>("topic", event.toByteArray()));
```

The `.proto` file IS the schema — find it via the generated class import.

### CSV / Delimited Strings

```java
String csv = orderId + "," + amount + "," + email;
```

Field names are NOT in the data — check comments, header rows, or variable names.

## Type Mapping

### To JSON Schema
- `String` → `"type": "string"`
- `int`/`long` → `"type": "integer"`
- `float`/`double` → `"type": "number"`
- `boolean` → `"type": "boolean"`
- `List`/`array` → `"type": "array"`
- `Map`/`object` → `"type": "object"`
- `Object`/`interface{}`/`any` → `"type": "string"` (default, add TODO)

Add:
- `"$schema": "http://json-schema.org/draft-07/schema#"`
- `"title"` matching class/model name
- `"required"` array for non-nullable fields

### To Avro
- `String` → `"string"`
- `int` → `"int"`
- `long` → `"long"`
- `float` → `"float"`
- `double` → `"double"`
- `boolean` → `"boolean"`
- `List` → `"array"`
- `Map` → `"map"`

Use:
- `"type": "record"` with `"namespace"` from package/module
- `["null", "type"]` union for nullable fields with `"default": null`

### To Protobuf
- `String` → `string`
- `int` → `int32`
- `long` → `int64`
- `float` → `float`
- `double` → `double`
- `boolean` → `bool`
- `List` → `repeated`
- `Map` → `map<K,V>`

Use `syntax = "proto3"` and `package` from namespace.

## PII Field Detection

### Patterns & Tags

The "Tag" column shows EXACT tags to use in `confluent:tags`.

| Pattern | Tag | Examples |
|---------|-----|---------|
| `email`, `e_mail`, `email_address`, `emailAddress` | `PII` | user_email, contact_email |
| `phone`, `phone_number`, `phoneNumber`, `mobile`, `telephone`, `tel` | `PII` | home_phone, mobile_number |
| `ssn`, `social_security`, `socialSecurity`, `social_security_number` | `PII`, `PRIVATE` | ssn_last4 |
| `name`, `first_name`, `firstName`, `last_name`, `lastName`, `full_name`, `fullName` | `PII` | customer_name |
| `address`, `street`, `city`, `state`, `zip`, `zip_code`, `zipCode`, `postal_code`, `postalCode` | `PII` | billing_address |
| `date_of_birth`, `dateOfBirth`, `dob`, `birth_date`, `birthday` | `PII` | customer_dob |
| `ip`, `ip_address`, `ipAddress`, `client_ip`, `remote_addr` | `PII` | source_ip |
| `credit_card`, `creditCard`, `card_number`, `cardNumber`, `ccn`, `pan` | `PII`, `PRIVATE` | payment_card_number |
| `passport`, `passport_number`, `passportNumber` | `PII`, `PRIVATE` | |
| `driver_license`, `driverLicense`, `license_number` | `PII`, `PRIVATE` | |
| `account_number`, `accountNumber`, `bank_account`, `iban`, `routing_number` | `PII`, `PRIVATE` | |
| `password`, `secret`, `token`, `api_key`, `apiKey` | `PRIVATE` | auth_token |
| `salary`, `income`, `compensation`, `wage` | `SENSITIVE` | annual_salary |
| `gender`, `sex`, `race`, `ethnicity`, `religion`, `nationality` | `SENSITIVE` | |
| `medical`, `diagnosis`, `prescription`, `health` | `SENSITIVE`, `PHI` | medical_record |

### Supported Tag Values

| Tag | Meaning |
|-----|---------|
| `PII` | Personally Identifiable Information |
| `PRIVATE` | Highly sensitive — should be encrypted or masked |
| `SENSITIVE` | Sensitive but not directly identifying |
| `PHI` | Protected Health Information (HIPAA) |
| `PUBLIC` | Safe for broad access |

### Tagging Examples

**Avro:**
```json
{
  "name": "email",
  "type": "string",
  "confluent:tags": ["PII"]
}
```

**JSON Schema:**
```json
{
  "email": {
    "type": "string",
    "confluent:tags": ["PII"]
  }
}
```

**Protobuf:**
```protobuf
import "confluent/meta.proto";

message Customer {
  string email = 1 [(confluent.field_meta).tags = "PII"];
  string ssn = 2 [
    (confluent.field_meta).tags = "PII",
    (confluent.field_meta).tags = "PRIVATE"
  ];
}
```

## Multi-Schema Topics

When multiple data models produce to the same topic, create a wrapper schema.

**JSON Schema wrapper:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "{TopicName}Event",
  "oneOf": [
    { "$ref": "{event-type-1}.json" },
    { "$ref": "{event-type-2}.json" }
  ]
}
```

**Avro wrapper:**
```json
[
  "{namespace}.EventType1",
  "{namespace}.EventType2"
]
```

**Protobuf wrapper:**
```protobuf
import "{event_type_1}.proto";
import "{event_type_2}.proto";

message {TopicName}Event {
  oneof event {
    EventType1 type1 = 1;
    EventType2 type2 = 2;
  }
}
```

Generate Terraform with `schema_reference` blocks pointing to individual event schemas.
