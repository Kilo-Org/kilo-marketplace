# Task-to-tool reference

Generated from the unchanged product MCP declarations. Parameter types and source hash are in TOOLS.json.

## upload_supplier_feed

Upload explicitly supplied UTF-8 CSV or JSONL (10 MiB, 50,000 records maximum). Stores it for 24 hours. No URL or local file paths.

- Task: Inspect the supplied original file
- Prerequisites: Explicit permission to read the source; remote upload also needs permission to transmit it
- Outputs: Upload identity/fingerprint or bounded inferred schema
- Approval: Source-file access/upload authorization
- Credits: No credits consumed
- Retry: Uploads create new identities; reuse the successful upload rather than uploading again

## preview_supplier_feed

Propose field mappings for an uploaded flat feed. Preview is not full validation or semantic approval.

- Task: Prepare decisions for review
- Prerequisites: Owned source plus explicit target rules/decisions
- Outputs: Unapproved proposal, version or sampled preview; not approval or full validation
- Approval: Do not infer business meanings; obtain missing decisions
- Credits: No credits consumed
- Retry: Reads/previews may repeat; saved drafts/versions can create new identities

## create_supplier_feed_profile

Save an unapproved versioned profile with explicit mapping, decimal locale, and quality rules.

- Task: Prepare decisions for review
- Prerequisites: Owned source plus explicit target rules/decisions
- Outputs: Unapproved proposal, version or sampled preview; not approval or full validation
- Approval: Do not infer business meanings; obtain missing decisions
- Credits: No credits consumed
- Retry: Reads/previews may repeat; saved drafts/versions can create new identities

## list_supplier_feed_profiles

List owned saved profile identities in pages of 50. Read a specific profile before reusing or approving it.

- Task: Read an owned result or decision
- Prerequisites: Existing owned resource and current account authorization
- Outputs: Structured result; inspect disclosed coverage and errors
- Approval: Read access within the user's task
- Credits: No credits consumed
- Retry: Read again using the same resource identity

## get_supplier_feed_profile

Read an owned profile's exact destination schema, approved decisions, contract, and version identity.

- Task: Read an owned result or decision
- Prerequisites: Existing owned resource and current account authorization
- Outputs: Structured result; inspect disclosed coverage and errors
- Approval: Read access within the user's task
- Credits: No credits consumed
- Retry: Read again using the same resource identity

## delete_supplier_feed_profile

Permanently delete an owned saved profile after explicit operator instruction. This does not start an evaluation or use credits.

- Task: Delete a saved decision
- Prerequisites: Existing owned resource and current account authorization
- Outputs: Deletion status; dependent pending jobs can fail safely
- Approval: Explicit deletion instruction and confirmation
- Credits: No credits consumed
- Retry: Read current state before retry; do not delete another version

## approve_supplier_feed_profile

Persist an explicit approval of the exact profile after the operator has resolved its field meanings and rules.

- Task: Record exact reviewed approval
- Prerequisites: Exact reviewed hash/fingerprint and scope, with all unresolved choices settled
- Outputs: Approval bound to that exact version
- Approval: Explicit authorized reviewer approval; fixture permission covers only owned fixtures
- Credits: No credits consumed
- Retry: Reuse only the same reviewed version and scope; edits invalidate approval

## quote_supplier_import

Quote one full-file evaluation against an approved profile. Detects source drift. Does not charge or start work.

- Task: Quote an approved complete-file evaluation
- Prerequisites: Owned upload and approved matching profile/contract/baseline
- Outputs: Quote, expiry, exact fingerprints and funding; drift can return review_required
- Approval: Approval required before quoting; quote does not start work
- Credits: No credits consumed
- Retry: Reuse the original quote/key for an uncertain started request; only quote anew for genuinely new work

## start_supplier_import

Start the quoted evaluation using one funded credit under the account cap. A completed rejection report is billable; platform failures release the credit.

- Task: Start one authorized complete-file evaluation
- Prerequisites: Unexpired funded quote and stable idempotency key
- Outputs: Durable job identity and status
- Approval: Explicit credit/spending authorization
- Credits: Reserves one product credit; supported completion (including rejection/block/warning) consumes one; platform failures release it
- Retry: Original quote AND original key; changed requests need a new quote/key; never start twice after a timeout

## get_supplier_import

Read an owned job's status and receipt. Does not initiate or repeat evaluation.

- Task: Read an owned result or decision
- Prerequisites: Existing owned resource and current account authorization
- Outputs: Structured result; inspect disclosed coverage and errors
- Approval: Read access within the user's task
- Credits: No credits consumed
- Retry: Read again using the same resource identity

## get_supplier_import_report

Read the complete-file validation report for an owned completed job during its seven-day result retention.

- Task: Read an owned result or decision
- Prerequisites: Existing owned resource and current account authorization
- Outputs: Structured result; inspect disclosed coverage and errors
- Approval: Read access within the user's task
- Credits: No credits consumed
- Retry: Read again using the same resource identity

## get_supplier_import_output

Read validated JSONL in pages of up to 500 records / 64 KiB for an owned passed job within seven days. Follow next_offset. Oversized records require an authenticated download of download_path.

- Task: Read validated JSONL
- Prerequisites: Passed owned job within seven-day output retention
- Outputs: Paged validated records; follow pagination to completion
- Approval: Downstream writes require separate authorization
- Credits: No credits consumed
- Retry: Read again using the same resource identity

