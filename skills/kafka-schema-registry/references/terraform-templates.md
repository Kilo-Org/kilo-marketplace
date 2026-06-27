# Terraform Templates Reference

Templates and structure for generating Confluent Terraform configurations.

See [Confluent Terraform Provider docs](https://registry.terraform.io/providers/confluentinc/confluent/latest/docs) for full reference.

## File Structure

**CRITICAL:** Create these separate files. Do NOT combine into main.tf:

```
terraform/
├── providers.tf              # Provider configuration only
├── variables.tf              # Variable definitions only
├── tags.tf                   # Tag resources (if PII exists)
├── schemas.tf                # Active schemas (Categories A, B, E)
├── flagged-auto-register.tf  # Category C only (commented out)
├── outputs.tf                # Output values only
└── import.sh                 # Import script for existing schemas
```

**Rules:**
- `schemas.tf` = Active schemas (A, B, E) — NOT commented out
- `flagged-auto-register.tf` = Category C ONLY — MUST be commented out
- `tags.tf` = MUST exist if ANY schema uses `confluent:tags`

## providers.tf

```hcl
terraform {
  required_version = ">= 1.3.0"

  required_providers {
    confluent = {
      source  = "confluentinc/confluent"
      version = "~> 2.0"
    }
  }
}

provider "confluent" {
  schema_registry_id            = var.schema_registry_id
  schema_registry_rest_endpoint = var.schema_registry_rest_endpoint
  schema_registry_api_key       = var.schema_registry_api_key
  schema_registry_api_secret    = var.schema_registry_api_secret
}
```

## variables.tf

```hcl
variable "schema_registry_id" {
  description = "Schema Registry cluster ID (e.g., lsrc-abc123)"
  type        = string
}

variable "schema_registry_rest_endpoint" {
  description = "Schema Registry REST endpoint URL"
  type        = string
}

variable "schema_registry_api_key" {
  description = "Schema Registry API key"
  type        = string
  sensitive   = true
}

variable "schema_registry_api_secret" {
  description = "Schema Registry API secret"
  type        = string
  sensitive   = true
}
```

## tags.tf

**MANDATORY IF ANY PII EXISTS.** Confluent Stream Governance requires tags to be created before schemas can use `confluent:tags`.

See [Stream Governance tags](https://docs.confluent.io/cloud/current/stream-governance/stream-catalog-rest-apis.md).

```hcl
# ──────────────────────────────────────────────
# Confluent Stream Governance Tags
# Must exist before schemas can use confluent:tags
# ──────────────────────────────────────────────

resource "confluent_tag" "pii" {
  name        = "PII"
  description = "Personally Identifiable Information — can identify an individual"
}

resource "confluent_tag" "private" {
  name        = "PRIVATE"
  description = "Highly sensitive data — should be encrypted or masked"
}

resource "confluent_tag" "sensitive" {
  name        = "SENSITIVE"
  description = "Sensitive information that requires restricted access"
}

resource "confluent_tag" "phi" {
  name        = "PHI"
  description = "Protected Health Information (HIPAA)"
}
```

Only include tags actually used in schemas.

## schemas.tf

For Category A, B, and E producers. **MANDATORY COMMENT BLOCK:**

```hcl
# ──────────────────────────────────────────────
# Topic: {topic_name}
# App: {app_name} ({language})
# Source: {file_path:line}
# Category: {A|B|E}
# ──────────────────────────────────────────────
resource "confluent_schema" "{sanitized_topic_name}_value" {
  subject_name = "{topic_name}-value"
  format       = "{AVRO|JSON|PROTOBUF}"
  schema       = file("../schemas/{format_dir}/{topic_name}-value.{ext}")

  # Only if schema uses confluent:tags
  depends_on = [confluent_tag.pii, confluent_tag.private]

  lifecycle {
    prevent_destroy = true
  }
}
```

**Resource naming:**
- Replace dots, hyphens, special chars with underscores
- Add `_value` or `_key` suffix

**Schema references** (multi-schema topics):
```hcl
  schema_reference {
    name         = "{referenced_type_name}"
    subject_name = "{referenced_subject}"
    version      = {version}
  }
```

## flagged-auto-register.tf

**CREATE ONLY IF Category C exists.** All resources MUST be commented out:

```hcl
# ╔══════════════════════════════════════════════════════════════╗
# ║  FLAGGED: auto.register.schemas=true                        ║
# ║                                                              ║
# ║  The following schemas are currently auto-registered by the  ║
# ║  producer at runtime. This is a risk because:                ║
# ║  - Schema evolution is uncontrolled                          ║
# ║  - Breaking changes can be registered accidentally           ║
# ║  - No review process for schema changes                      ║
# ║                                                              ║
# ║  To fix:                                                     ║
# ║  1. Set auto.register.schemas=false in the producer config   ║
# ║  2. Uncomment the resources below                            ║
# ║  3. Run terraform apply to register schemas via IaC          ║
# ║  4. Set use.latest.version=true in the producer config       ║
# ╚══════════════════════════════════════════════════════════════╝

# ──────────────────────────────────────────────
# Topic: {topic_name}
# App: {app_name} ({language})
# auto.register.schemas=true found at: {file}:{line}
# ──────────────────────────────────────────────
# resource "confluent_schema" "{sanitized_topic_name}_value" {
#   subject_name = "{topic_name}-value"
#   format       = "{AVRO|JSON|PROTOBUF}"
#   schema       = file("../schemas/{format_dir}/{topic_name}-value.{ext}")
#
#   lifecycle {
#     prevent_destroy = true
#   }
# }
```

## outputs.tf

```hcl
# Outputs for each registered schema (uncommented resources only)
output "{sanitized_topic_name}_value_schema_id" {
  description = "Schema ID for {topic_name}-value"
  value       = confluent_schema.{sanitized_topic_name}_value.schema_identifier
}

output "{sanitized_topic_name}_value_version" {
  description = "Schema version for {topic_name}-value"
  value       = confluent_schema.{sanitized_topic_name}_value.version
}
```

## import.sh

For schemas already in SR (Category A, C):

```bash
#!/bin/bash
# Import existing schemas from Schema Registry into Terraform state.
# Set these environment variables before running:
#   IMPORT_SCHEMA_REGISTRY_API_KEY
#   IMPORT_SCHEMA_REGISTRY_API_SECRET
#   IMPORT_SCHEMA_REGISTRY_REST_ENDPOINT

# {Repeat for each schema already in SR}
terraform import confluent_schema.{resource_name} "{sr_cluster_id}/{subject_name}/latest"
```

## File Naming Convention

**CRITICAL:** All schema files MUST use **kebab-case** (lowercase with hyphens).

- Value schemas: `{topic}-value.{ext}`
- Key schemas: `{topic}-key.{ext}`
- Extensions: `.avsc` (Avro), `.json` (JSON Schema), `.proto` (Protobuf)

**Conversion examples:**
- `OrderCreatedEvent` → `order-created-event-value.avsc` ✓
- `user_notifications` → `user-notifications-value.json` ✓
- ❌ WRONG: `OrderCreatedEvent-value.avsc` (PascalCase)
- ❌ WRONG: `user_notifications-value.json` (snake_case)
