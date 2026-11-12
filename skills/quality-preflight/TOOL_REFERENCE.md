# Task-to-tool reference

Generated from the unchanged product MCP declarations. Parameter types and source hash are in TOOLS.json.

## upload_quality_file

Upload the ACTUAL original UTF-8 flat csv/jsonl file, at most 10 MiB/50,000 records/100 fields. Stored 24h. A profile/summary/URL/server path cannot stand in for a complete file.

- Task: Inspect the supplied original file
- Prerequisites: Explicit permission to read the source; remote upload also needs permission to transmit it
- Outputs: Upload identity/fingerprint or bounded inferred schema
- Approval: Source-file access/upload authorization
- Credits: No credits consumed
- Retry: Uploads create new identities; reuse the successful upload rather than uploading again

## draft_quality_contract

Save a new unapproved contract version with explicit field types, numeric locale, null decisions and stable rule IDs/actions. Supported: not_null, unique, accepted_values, null_rate, row_count, range. Review before approval.

- Task: Prepare decisions for review
- Prerequisites: Owned source plus explicit target rules/decisions
- Outputs: Unapproved proposal, version or sampled preview; not approval or full validation
- Approval: Do not infer business meanings; obtain missing decisions
- Credits: No credits consumed
- Retry: Reads/previews may repeat; saved drafts/versions can create new identities

## get_quality_contract

Read an owned contract's exact decisions and approval hash/version before reuse.

- Task: Read an owned result or decision
- Prerequisites: Existing owned resource and current account authorization
- Outputs: Structured result; inspect disclosed coverage and errors
- Approval: Read access within the user's task
- Credits: No credits consumed
- Retry: Read again using the same resource identity

## list_quality_contracts

List owned contract identities in pages of 50; read the full contract before reviewing or approving it.

- Task: Read an owned result or decision
- Prerequisites: Existing owned resource and current account authorization
- Outputs: Structured result; inspect disclosed coverage and errors
- Approval: Read access within the user's task
- Credits: No credits consumed
- Retry: Read again using the same resource identity

## delete_quality_decision

Delete an owned contract or baseline after explicit operator instruction. kind is quality_contract or quality_baseline. Pending checks using it fail safely. Does not start a check or consume credits.

- Task: Delete a saved decision
- Prerequisites: Existing owned resource and current account authorization
- Outputs: Deletion status; dependent pending jobs can fail safely
- Approval: Explicit deletion instruction and confirmation
- Credits: No credits consumed
- Retry: Read current state before retry; do not delete another version

## approve_quality_contract

Approve this exact contract hash only after operator authorization and review of destination meanings, locale, nulls, actions and disclosed coverage.

- Task: Record exact reviewed approval
- Prerequisites: Exact reviewed hash/fingerprint and scope, with all unresolved choices settled
- Outputs: Approval bound to that exact version
- Approval: Explicit authorized reviewer approval; fixture permission covers only owned fixtures
- Credits: No credits consumed
- Retry: Reuse only the same reviewed version and scope; edits invalidate approval

## draft_quality_baseline

Draft a versioned row-count baseline from the actual owned reference file for an approved contract declaring a threshold/action. Never replaces a baseline automatically.

- Task: Prepare decisions for review
- Prerequisites: Owned source plus explicit target rules/decisions
- Outputs: Unapproved proposal, version or sampled preview; not approval or full validation
- Approval: Do not infer business meanings; obtain missing decisions
- Credits: No credits consumed
- Retry: Reads/previews may repeat; saved drafts/versions can create new identities

## approve_quality_baseline

Approve the reviewed exact baseline hash for its specific contract after operator authorization.

- Task: Record exact reviewed approval
- Prerequisites: Exact reviewed hash/fingerprint and scope, with all unresolved choices settled
- Outputs: Approval bound to that exact version
- Approval: Explicit authorized reviewer approval; fixture permission covers only owned fixtures
- Credits: No credits consumed
- Retry: Reuse only the same reviewed version and scope; edits invalidate approval

## get_quality_baseline

Read owned baseline reference-file fingerprint, row count and approval/version.

- Task: Read an owned result or decision
- Prerequisites: Existing owned resource and current account authorization
- Outputs: Structured result; inspect disclosed coverage and errors
- Approval: Read access within the user's task
- Credits: No credits consumed
- Retry: Read again using the same resource identity

## quote_quality_check

Quote one entire-file check with exact approved versions and original SHA256, expiring in 10 minutes. Completed blocks/warnings cost one quality credit ($20/100); errors/platform failures are free. Does not start work.

- Task: Quote an approved complete-file evaluation
- Prerequisites: Owned upload and approved matching profile/contract/baseline
- Outputs: Quote, expiry, exact fingerprints and funding; drift can return review_required
- Approval: Approval required before quoting; quote does not start work
- Credits: No credits consumed
- Retry: Reuse the original quote/key for an uncertain started request; only quote anew for genuinely new work

## start_quality_check

Authorize a quoted full-file preflight and reserve one QUALITY credit under the quality cap. Reuse this quote/key on retries. Completed continue/warning/block consumes one; errors release it. Feed credits cannot fund this.

- Task: Start one authorized complete-file evaluation
- Prerequisites: Unexpired funded quote and stable idempotency key
- Outputs: Durable job identity and status
- Approval: Explicit credit/spending authorization
- Credits: Reserves one product credit; supported completion (including rejection/block/warning) consumes one; platform failures release it
- Retry: Original quote AND original key; changed requests need a new quote/key; never start twice after a timeout

## get_quality_check

Read an owned job and operational receipt; does not start another check. Downstream writes proceed only on continue by default.

- Task: Read an owned result or decision
- Prerequisites: Existing owned resource and current account authorization
- Outputs: Structured result; inspect disclosed coverage and errors
- Approval: Read access within the user's task
- Credits: No credits consumed
- Retry: Read again using the same resource identity

## get_quality_report

Read the completed full-file report for seven days: record count, rules, redacted failure counts and bounded record references. This report is NOT the original dataset.

- Task: Read an owned result or decision
- Prerequisites: Existing owned resource and current account authorization
- Outputs: Structured result; inspect disclosed coverage and errors
- Approval: Read access within the user's task
- Credits: No credits consumed
- Retry: Read again using the same resource identity

## get_checked_original_download

Get the authenticated original-data download path after continue, while the 24h source retention remains. SHA256 identifies the actual checked bytes; never forward report JSON as customer data.

- Task: Fetch the checked original
- Prerequisites: Owned continue job and original still within 24-hour retention
- Outputs: Authenticated download path and original SHA256; verify downloaded bytes
- Approval: Only continue permits downstream writes by default; separate destination authorization
- Credits: No credits consumed
- Retry: Read again using the same resource identity

## quality_wallet

Read separate quality credits, cap, low balance and funding link. Five trials once per verified organization; $20/100 prepaid checks, no subscription/automatic replenishment.

- Task: Read an owned result or decision
- Prerequisites: Existing owned resource and current account authorization
- Outputs: Structured result; inspect disclosed coverage and errors
- Approval: Read access within the user's task
- Credits: No credits consumed
- Retry: Read again using the same resource identity

## quality_billing_status

Read payment activation state for quality. Sandbox/internal qualification does not establish live activation or customer purchases.

- Task: Read an owned result or decision
- Prerequisites: Existing owned resource and current account authorization
- Outputs: Structured result; inspect disclosed coverage and errors
- Approval: Read access within the user's task
- Credits: No credits consumed
- Retry: Read again using the same resource identity

## quality_purchase_history

Read owned quality purchase snapshots, settlement mode and refund state. A pack sale is one purchase of 100 credits; sandbox purchases do not establish live revenue.

- Task: Read an owned result or decision
- Prerequisites: Existing owned resource and current account authorization
- Outputs: Structured result; inspect disclosed coverage and errors
- Approval: Read access within the user's task
- Credits: No credits consumed
- Retry: Read again using the same resource identity

