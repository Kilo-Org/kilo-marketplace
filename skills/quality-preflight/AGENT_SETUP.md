# Data Quality Gate agent setup

Reviewed documentation: 2026-11-01. Examples contain placeholders, never live credentials.

## Install and authenticate

Verify your email, activate this product and create an organization key in the existing account portal. Set QUALITY_API_KEY privately in the client environment. Never paste its value in prompts, public files or shell history. Codex CLI and Claude Code must be installed and signed in with existing client accounts. Missing/empty credentials must stop setup; OAuth and machine payments are not enabled. Account portal: https://mcp.contentsweep.ai/account/sign-in?product=data-quality-gate&source=agent-skill&channel=owned-agent&asset=quality-preflight&campaign=quality-lead-preflight-60d. Owned examples and installation source: https://github.com/founder-sweep/data-quality-gate-examples. Existing n8n recipes: https://mcp.contentsweep.ai/quality/workflows.

Copy this reviewed skill bundle into .agents/skills/quality-preflight/ for Codex or .claude/skills/quality-preflight/ for Claude Code in the intended project. Copy the supporting AGENT_SETUP.md, TOOL_REFERENCE.md, TOOLS.json and client examples with it. Codex user-wide skills can instead live in ~/.agents/skills; Claude Code user-wide skills in ~/.claude/skills. Merge the Codex entry into the chosen isolated profile config.toml or reviewed ~/.codex/config.toml; merge Claude entries into project .mcp.json. Never overwrite unrelated settings. Review existing settings before merging a server entry; do not replace an entire configuration file. Restart or create a fresh client session and confirm tool discovery.

## Codex configuration

```toml
[mcp_servers."quality-preflight"]
url = "https://mcp.contentsweep.ai/v1/quality/mcp/"
env_http_headers = { "X-API-Key" = "QUALITY_API_KEY" }
```

## Claude Code configuration

```json
{
  "mcpServers": {
    "quality-preflight": {
      "type": "http",
      "url": "https://mcp.contentsweep.ai/v1/quality/mcp/",
      "headers": {
        "X-API-Key": "${QUALITY_API_KEY}"
      }
    }
  }
}
```

## Synthetic first task

Use the repository-owned leads.csv and leads.contract.json. Compare the passing fixture with the duplicate-near-end and warning guides at https://mcp.contentsweep.ai/quality/guides. Never substitute a profile or sampled summary for the original file.

## Workflow

Upload the actual original bytes; draft and review the exact contract and any baseline; obtain authorized hash approval; quote; obtain authorization to use one Quality credit; start with a stable retry key; poll within a bounded deadline. Continue downstream only on continue. Download the checked original and verify its SHA256 against the receipt before writing those exact bytes. The report is not the dataset. Hash scopes differ: contract.hash, quote.contract_hash and receipt.contract_hash identify the versioned approval decision; report.contract_hash hashes only its embedded normalized contract body. Those two hash scopes normally differ, so do not compare them directly. Verify original bytes using upload.sha256, input_fingerprint in quote/receipt/report/download metadata, and the downloaded original SHA256.

## Recovery and credit effects

Warnings, blocks, errors, unknown statuses and timeouts stop downstream writes for review. Completed warnings/blocks consume one check; unsupported/incomplete/platform failures are free. Resume an uncertain request using its original quote and key; do not create a second charge. Corrected bytes require a new upload, quote and key. Originals expire after 24 hours, reports after seven days and receipts after 30 days.

## Price and bounds

Five trials once per verified organization; $20 plus applicable tax for 100 completed checks. No subscription or automatic replenishment.

Flat UTF-8 CSV/JSONL, 10 MiB, 50,000 records, 100 fields. No repair, remapping or independent business-meaning verification.

Official client references: https://learn.chatgpt.com/docs/extend/mcp?surface=cli and https://code.claude.com/docs/en/mcp. Skill installation references: https://learn.chatgpt.com/docs/build-skills and https://code.claude.com/docs/en/skills.

Configuration, actual MCP execution and paid customer adoption are different outcomes. Qualification fixtures and internal accounts are not customers.

## Optional account and funding workflow

Open https://mcp.contentsweep.ai/account/sign-in?product=data-quality-gate&source=agent-skill&channel=skills&asset=contentsweep-quality&campaign=agent-growth-v1. The operator verifies email and creates an organization API key. Load QUALITY_API_KEY privately; never put a key in a URL, transcript or source control.

Configure Streamable HTTP MCP at https://mcp.contentsweep.ai/v1/quality/mcp/ with X-API-Key. Initialization and tools/list also require the key; anonymous 401 means authentication is required. There is no OAuth or machine-payment flow.

Five trial checks once per verified organization. Thereafter $20 plus applicable tax buys 100 checks. A completed continue, warning or block costs one check; platform/incomplete/unsupported failures release it. No subscription or automatic replenishment. Credits are product-specific. Read quality_wallet and quality_billing_status; if funding is needed, hand the operator https://mcp.contentsweep.ai/quality/app?source=agent-skill&channel=skills&asset=contentsweep-quality&campaign=agent-growth-v1. Obtain approval for the displayed purchase; never enter card details or buy automatically.
