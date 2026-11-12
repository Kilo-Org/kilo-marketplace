# Task-to-tool reference

Generated from the unchanged product MCP declarations. Parameter types and source hash are in TOOLS.json.

## infer_schema

Infer flat schema from a bounded local CSV/JSON/JSONL file.

- Task: Inspect the supplied original file
- Prerequisites: Explicit permission to read the source; remote upload also needs permission to transmit it
- Outputs: Upload identity/fingerprint or bounded inferred schema
- Approval: Source-file access/upload authorization
- Credits: No credits consumed
- Retry: Uploads create new identities; reuse the successful upload rather than uploading again

## map_to_schema

Propose correspondence; strict JSON strings preserve decimal precision.

- Task: Prepare decisions for review
- Prerequisites: Owned source plus explicit target rules/decisions
- Outputs: Unapproved proposal, version or sampled preview; not approval or full validation
- Approval: Do not infer business meanings; obtain missing decisions
- Credits: No credits consumed
- Retry: Reads/previews may repeat; saved drafts/versions can create new identities

## review_mapping

Inspect exact proposal, evidence, alternatives and approval state.

- Task: Review validity, drift or correspondences
- Prerequisites: Exact proposed/approved mapping, explicit target/source and matching scope where required
- Outputs: Validation/review/drift report; stop on unsupported or mismatched inputs
- Approval: Read access within the user's task
- Credits: No credits consumed
- Retry: Safe to repeat unchanged validation; changed decisions need review

## resolve_mapping

Explicit target:source decisions; null skips an optional target.

- Task: Prepare decisions for review
- Prerequisites: Owned source plus explicit target rules/decisions
- Outputs: Unapproved proposal, version or sampled preview; not approval or full validation
- Approval: Do not infer business meanings; obtain missing decisions
- Credits: No credits consumed
- Retry: Reads/previews may repeat; saved drafts/versions can create new identities

## approve_mapping

Record user-authorized review of an exact mapping for a named scope.

- Task: Record exact reviewed approval
- Prerequisites: Exact reviewed hash/fingerprint and scope, with all unresolved choices settled
- Outputs: Approval bound to that exact version
- Approval: Explicit authorized reviewer approval; fixture permission covers only owned fixtures
- Credits: No credits consumed
- Retry: Reuse only the same reviewed version and scope; edits invalidate approval

## validate_schema_mapping

Check schema, completeness, exact fingerprints, decisions and approval.

- Task: Review validity, drift or correspondences
- Prerequisites: Exact proposed/approved mapping, explicit target/source and matching scope where required
- Outputs: Validation/review/drift report; stop on unsupported or mismatched inputs
- Approval: Read access within the user's task
- Credits: No credits consumed
- Retry: Safe to repeat unchanged validation; changed decisions need review

## check_schema_drift

Compare a local input schema against approved scope and schema version.

- Task: Review validity, drift or correspondences
- Prerequisites: Exact proposed/approved mapping, explicit target/source and matching scope where required
- Outputs: Validation/review/drift report; stop on unsupported or mismatched inputs
- Approval: Read access within the user's task
- Credits: No credits consumed
- Retry: Safe to repeat unchanged validation; changed decisions need review

## transform_file

Transform an approved local snapshot; return exact JSON and receipt.

- Task: Create a reusable local output
- Prerequisites: Reviewed approved mapping with matching fingerprint/scope; validate first
- Outputs: Exact transformed records and receipt, or matching-runtime Python wrapper text; MCP does not save an output file
- Approval: Explicit mapping approval and read access; saving output or executing a generated wrapper requires its own authorization
- Credits: No credits consumed
- Retry: Repeat only for the same approved mapping and scope; the caller must deliberately save returned data if requested

## generate_transformation

Emit approved runtime-dependent Python; never executes supplied code.

- Task: Create a reusable local output
- Prerequisites: Reviewed approved mapping with matching fingerprint/scope; validate first
- Outputs: Exact transformed records and receipt, or matching-runtime Python wrapper text; MCP does not save an output file
- Approval: Explicit mapping approval and read access; saving output or executing a generated wrapper requires its own authorization
- Credits: No credits consumed
- Retry: Repeat only for the same approved mapping and scope; the caller must deliberately save returned data if requested

