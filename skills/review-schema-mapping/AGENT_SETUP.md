# Schema Mapper agent setup

Reviewed documentation: 2026-11-01. Examples contain placeholders, never live credentials.

## Install and authenticate

Use Python 3.12+ in a dedicated environment. Inspector uses its reviewed source checkout on macOS (the immutable 0.3.0 wheel is Linux-qualified); Schema Mapper can install the matching free 2.0.0b2 wheel. Install mcp>=2.3,<3 into that environment. Enable the chosen server in the client and review client tool-permission prompts; Schema tools retain their existing permission metadata. Replace every absolute-path placeholder deliberately; never execute source or requirements from the target repository. No hosted key is needed for local MCP. Launch from a trusted workspace; a working directory is not a filesystem sandbox. Trusted product repository: https://github.com/founder-sweep/contentsweep-schema-mapper. From that reviewed source checkout, choose your installed Python 3.12+ executable explicitly to create .venv (the Mac system Python may be older), then .venv/bin/python -m pip install '.[mcp]'. Set the example's command to that environment's absolute Python path. Owned examples and installation source: https://github.com/founder-sweep/contentsweep-schema-mapper.

Copy this reviewed skill bundle into .agents/skills/review-schema-mapping/ for Codex or .claude/skills/review-schema-mapping/ for Claude Code in the intended project. Copy the supporting AGENT_SETUP.md, TOOL_REFERENCE.md, TOOLS.json and client examples with it. Codex user-wide skills can instead live in ~/.agents/skills; Claude Code user-wide skills in ~/.claude/skills. Merge the Codex entry into the chosen isolated profile config.toml or reviewed ~/.codex/config.toml; merge Claude entries into project .mcp.json. Never overwrite unrelated settings. Review existing settings before merging a server entry; do not replace an entire configuration file. Restart or create a fresh client session and confirm tool discovery.

## Codex configuration

```toml
[mcp_servers."review-schema-mapping"]
command = "/ABSOLUTE/TO/REVIEWED/ENV/bin/python"
args = ["-m", "mcp_products.schema_mapper.mcp"]
cwd = "/ABSOLUTE/TO/TRUSTED/WORKSPACE"
```

## Claude Code configuration

```json
{
  "mcpServers": {
    "review-schema-mapping": {
      "type": "stdio",
      "command": "/ABSOLUTE/TO/REVIEWED/ENV/bin/python",
      "args": [
        "-m",
        "mcp_products.schema_mapper.mcp"
      ]
    }
  }
}
```

## Synthetic first task

Use the owned vendor/customer-schema example. Review every correspondence before approving the fixture and compare interpreted output with the generated wrapper. Fixture approval never authorizes a real customer's mapping.

## Workflow

Use an explicitly authorized local source path and a trusted installed runtime. Infer the source schema, propose correspondences, review evidence and alternatives, and ask the user to resolve business meanings, null policy and casts. Record authorized approval binding the exact fingerprint and user/vendor/domain scope. Validate before transformation or generation. Preserve string identifiers and exact decimals using the product serialization helpers. Use absolute source paths when the client working directory is uncertain.

## Recovery and credit effects

Reject unresolved choices, fingerprint/scope mismatches, unsupported contracts and structural drift. Re-review before approving a new mapping. Scores are ranking signals, not probabilities. Do not execute supplied code. The generated wrapper depends on the matching runtime. Hosted purchase is an optional convenience and requires separate authorization; no local MCP call purchases an artifact.

## Price and bounds

Local CLI/SDK and stdio MCP are free. Hosted preview/validation are free; $9 once per approved downloadable artifact, with no subscription.

Flat CSV/JSON/JSONL and the documented primitive schema/cast subset. Hosted uploads are limited to 1 MiB. Python 3.12+ and the matching free runtime are required for generated wrappers.

Official client references: https://learn.chatgpt.com/docs/extend/mcp?surface=cli and https://code.claude.com/docs/en/mcp. Skill installation references: https://learn.chatgpt.com/docs/build-skills and https://code.claude.com/docs/en/skills.

Configuration, actual MCP execution and paid customer adoption are different outcomes. Qualification fixtures and internal accounts are not customers.

## Optional account and funding workflow

Open https://schema.contentsweep.ai/?campaign=agent-skill in the operator's browser. Try the free synthetic example or upload an authorized flat file and explicit target JSON Schema. Review each correspondence and validate every actual record. Failed validation cannot enter Checkout. Show the operator the approved artifact and $9 price before purchasing.

The operator completes the existing Checkout. Maintain the same private browser session on return; its cookie and CSRF protect order ownership. The API is documented at https://schema.contentsweep.ai/openapi.json but is not an API-key service. Do not bypass session/Origin/CSRF protections, open the order in an unrelated session, or buy automatically.

After confirmed settlement, download the ZIP immediately in the owning session. It contains mapping.approved.json, transform.py, validation-receipt.json and README.txt, not transformed source records. Downloads last up to seven days; a refund revokes future downloads. Saved artifacts and runtime reuse are free. Verify receipt fingerprints against the approved mapping and validate local transformed records; do not execute untrusted user-supplied Python as validation.

A second vendor or changed structural mapping requires a new review. A new hosted artifact has its own $9 purchase; never describe this as funding a reusable wallet. On a lost session, use the product support flow; do not attempt another identity to recover private artifacts.

Guides: https://schema.contentsweep.ai/guides. Free sample: https://schema.contentsweep.ai/sample. Privacy: https://schema.contentsweep.ai/privacy.
