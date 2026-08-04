# Producer Categorization Reference

Classify each producer into a category based on current state and required actions.

## Category Definitions

| Category | Criteria | Action |
|----------|----------|--------|
| **A: Compliant** | Uses Confluent serializer + schema.registry.url configured + no auto.register | Report as compliant. Still extract schema to Terraform if not already managed by IaC. |
| **A→Header: Already on SR, migrating to headers** | Uses Confluent serializer + SR, wants to move schema ID from payload prefix to Kafka headers | No schema extraction needed. Add `HeaderSchemaIdSerializer` to producers. Consumers need no changes — Confluent deserializers automatically check both. |
| **B: Schema in code, no SR** | Has data models/classes but uses StringSerializer, JsonSerializer (Spring), kafka-python, kafkajs raw, or no Confluent SR integration | Extract schema → `terraform/schemas.tf` + add upgrade recommendation |
| **C: Auto-register** | Has `auto.register.schemas=true` | Extract schema → `terraform/flagged-auto-register.tf` (commented out) + flag risk |
| **D: No schema** | Raw strings/bytes, no discernible data model, hardcoded JSON strings | Flag in report with recommendation to adopt schema-first approach |
| **E: Custom serializer** | Implements `Serializer<T>` interface, uses `json.dumps`/`JSON.stringify`/`JsonConvert`/`json.Marshal`/`GenericDatumWriter` inline — all without SR | Extract schema from data model → `terraform/schemas.tf` + recommend replacing with Confluent serializer |

## App Catalog Structure

For each Kafka application:
```yaml
app_name: directory or module name
language: Java | Python | .NET | Go | Node/TS
role: producer | consumer | both
topics: [list of topic names]
serializer_class: the value.serializer being used
custom_serializer: true | false
custom_serializer_file: file:line where defined
schema_format: AVRO | JSON | PROTOBUF | UNKNOWN
sr_integrated: true | false
sr_url: schema registry URL if configured
auto_register: true | false
category: A | B | C | D | E
```

## Category Labeling Requirements

**CRITICAL:** Use the exact phrase "Category X" in these locations:

1. **App catalog** — internal field: `category: "C"`
2. **Applications Discovered table** — Category column showing the letter
3. **Report section headers** — "order-processor — Category C"
4. **Upgrade recommendations** — Include "Category X" in heading/first paragraph
5. **Terraform comments** — `# Category: C` line
6. **Risk sections** — "Category C applications with auto-registration..."

**Examples:**
- ✅ "The order-processor application is **Category C** (auto-register)"
- ✅ Terraform comment: `# Category: C`
- ❌ WRONG: "The application uses auto-registration" (missing "Category C")

## Migration Rollout Order by Category

### Category B (JSON data, no SR) — Producers First

Consumers today read raw JSON and ignore headers. Safe to upgrade producers first.

1. **Upgrade producers** → Confluent serializer + `HeaderSchemaIdSerializer`
2. **Upgrade consumers** → Confluent deserializer (auto-detects schema ID location)

### Category A→Header (Already on SR) — Producers Only

Consumers already use Confluent deserializers. On supported versions, they auto-check headers first.

1. **Verify consumer versions** — Java 8.1.1+, Python 2.13.0+, etc.
2. **Upgrade producers** — add `HeaderSchemaIdSerializer`

### Category C (Auto-register) — Producers First

Similar to Category B — disable auto-register, register via Terraform, producers fetch latest.

1. **Register schemas via Terraform**
2. **Set auto.register.schemas=false** in producer config
3. **Set use.latest.version=true** in producer config

### Category E (Custom serializers) — Consumers First

Payload format changes when replacing custom serializers.

1. **Upgrade consumers** — Java: composite deserializer. Others: coordinated cutover
2. **Upgrade producers** — replace custom serializer with Confluent + `HeaderSchemaIdSerializer`
3. **After old data expires** — remove composite deserializer

## Minimum Client Versions

For header-based schema ID (`HeaderSchemaIdSerializer`):

- Java: CP client >= 8.1.1
- C/C++: libserdes >= 0.1.0
- Python: confluent-kafka >= 2.13.0
- .NET: Confluent.Kafka >= 2.13.0
- Go: confluent-kafka-go >= 2.13.0
- Node.js: @confluentinc/kafka-javascript >= 1.8.0

**Consumer auto-detection:** All Confluent deserializers on supported versions automatically check Kafka headers first for schema ID, then fall back to payload prefix.
