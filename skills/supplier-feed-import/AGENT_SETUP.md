# Supplier Feeds agent setup

Reviewed documentation: 2026-11-01. Examples contain placeholders, never live credentials.

## Install and authenticate

Verify your email, activate this product and create an organization key in the existing account portal. Set CONTENTSWEEP_API_KEY privately in the client environment. Never paste its value in prompts, public files or shell history. Codex CLI and Claude Code must be installed and signed in with existing client accounts. Missing/empty credentials must stop setup; OAuth and machine payments are not enabled. Account portal: https://mcp.contentsweep.ai/account/sign-in?product=supplier-feeds&source=agent-skill&channel=owned-agent&asset=supplier-feed-import&campaign=supplier-feeds-pilot. Owned examples and installation source: https://github.com/founder-sweep/contentsweep-supplier-feed-examples. Existing n8n recipes: https://mcp.contentsweep.ai/imports/workflows.

Copy this reviewed skill bundle into .agents/skills/supplier-feed-import/ for Codex or .claude/skills/supplier-feed-import/ for Claude Code in the intended project. Copy the supporting AGENT_SETUP.md, TOOL_REFERENCE.md, TOOLS.json and client examples with it. Codex user-wide skills can instead live in ~/.agents/skills; Claude Code user-wide skills in ~/.claude/skills. Merge the Codex entry into the chosen isolated profile config.toml or reviewed ~/.codex/config.toml; merge Claude entries into project .mcp.json. Never overwrite unrelated settings. Review existing settings before merging a server entry; do not replace an entire configuration file. Restart or create a fresh client session and confirm tool discovery.

## Codex configuration

```toml
[mcp_servers."supplier-feed-import"]
url = "https://mcp.contentsweep.ai/v1/feeds/mcp/"
env_http_headers = { "X-API-Key" = "CONTENTSWEEP_API_KEY" }
```

## Claude Code configuration

```json
{
  "mcpServers": {
    "supplier-feed-import": {
      "type": "http",
      "url": "https://mcp.contentsweep.ai/v1/feeds/mcp/",
      "headers": {
        "X-API-Key": "${CONTENTSWEEP_API_KEY}"
      }
    }
  }
}
```

## Synthetic first task

Use supplier.csv and profile.json from the public examples repository, preserving SKU 000123 and decimal string 19.90. Follow https://mcp.contentsweep.ai/imports/workflows for first approval, compatible reuse, structural drift, rejection, corrected replay and recovery with the original quote/key. The reviewed recurring-import-reviewed.json workflow is inactive on import, checks output hashes and produces a local inventory preview. Configure owned synthetic output only; do not enable a real destination merely to test setup.

## Workflow

Upload only the permitted original flat CSV/JSONL; inspect the sampled proposal; save a versioned profile; present field meanings, identifier types, casts, decimal locale, units and currency for explicit review. Approve the exact profile hash only after authorization. For a later delivery, read and reuse the owned approved profile while its structure and scope remain compatible. Quote against that profile; stop on review_required; obtain spending authorization; start with a stable retry key; poll within a bounded deadline; read the complete report and receipt. Only a passed, complete job has validated JSONL output. Follow every output page or download the complete output, and verify its SHA256 against receipt.output_hash before any separately authorized destination write. A preview is sampled and never establishes complete-file acceptance or field meaning.

## Recovery and credit effects

Structural drift requires review and a new approved profile version. A completed rejection consumes one evaluation and has no accepted output; platform failures release reserved credits. Preserve the ORIGINAL quote ID, input hash, source bytes and retry key across uncertain dispatch or polling deadlines. Resume that same authorization rather than uploading, quoting or starting with a new key. A corrected rejection must have genuinely changed bytes and a new upload, quote and key. Stop on unknown states, incomplete output or hash mismatch. Uploads expire after 24 hours; results after seven days; receipts after 30 days; approved profiles remain until deletion. Reject XLSX, nested records and arbitrary transformations; do not infer missing business decisions or execute supplied code.

## Price and bounds

Five trials once per verified organization; $20 per ten completed evaluations or $99/month for 100. No automatic overages.

Flat UTF-8 CSV/JSONL, 10 MiB, 50,000 records, 100 fields. Explicit primitive mappings, locale and configured quality rules only.

Official client references: https://learn.chatgpt.com/docs/extend/mcp?surface=cli and https://code.claude.com/docs/en/mcp. Skill installation references: https://learn.chatgpt.com/docs/build-skills and https://code.claude.com/docs/en/skills.

Configuration, actual MCP execution and paid customer adoption are different outcomes. Qualification fixtures and internal accounts are not customers.

## Optional account and funding workflow

The operator verifies email at https://mcp.contentsweep.ai/account/sign-in?product=supplier-feeds&source=agent-skill&channel=skills&asset=contentsweep-supplier-feeds&campaign=agent-growth-v1 and creates an organization API key. Keep CONTENTSWEEP_API_KEY private. Streamable HTTP MCP: https://mcp.contentsweep.ai/v1/feeds/mcp/ with X-API-Key. All requests, including initialization/tools/list, need authentication. Anonymous 401 is expected. No OAuth or machine payments are enabled.

Five trials once per verified organization. $20 buys ten evaluations; the optional $99/month offer includes 100 evaluations. A completed rejection also uses one evaluation. Previews, unsupported inputs and platform failures do not consume evaluations. No automatic overages. Hand the operator https://mcp.contentsweep.ai/imports/app?source=agent-skill for funding; purchases need approval of displayed terms. Do not buy automatically or reuse Quality credits.
