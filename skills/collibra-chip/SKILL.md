---
name: "collibra-chip"
description: "This skill should be used when a connected Collibra Chip MCP server can provide domain-specific Collibra workflows and references."
metadata:
  category: data
  source:
    repository: "https://github.com/collibra/chip"
    path: "SKILLS.md"
    license_path: "LICENSE"
---

# Collibra Chip MCP Skill Discovery

Collibra Chip serves its detailed guides at runtime through MCP. This package is a Kilo-facing routing guide; it does not contain an upstream source tree or embedded copies of the Collibra guides.

## Required Tools

Use the connected Chip MCP server's advertised tools. The expected capabilities are:

- `list_collibra_skills`: discover available guides and descriptions
- `load_collibra_skill`: load a guide body, metadata, or one of its bundled references

Tool names can be namespaced by the MCP client. Match by the advertised tool name and schema rather than hard-coding a namespace.

## Workflow

1. Confirm that the Collibra Chip MCP server is connected.
2. Call `list_collibra_skills`, requesting descriptions when the schema supports that option.
3. If the task is ambiguous, select the catalog/index guide first. Otherwise choose the narrowest matching guide.
4. Call `load_collibra_skill` for that guide's body.
5. Load a bundled reference only when the guide identifies it as necessary.
6. Follow the loaded guide and the live MCP tool schemas. Do not infer operation names, UUID formats, or mutation payloads from this router.

## Common Routing Topics

Depending on the server version, the catalog may include guides for discovery, technical lineage, asset creation, and asset editing. Treat this list as orientation only; the result of `list_collibra_skills` is authoritative.

- Discovery: semantic versus keyword search and resolving names to UUIDs
- Lineage: technical lineage and identifier bridging
- Asset creation: duplicate checks, required fields, and rich-text handling
- Asset editing: supported operation types and safe update sequencing

## Safety

- Resolve human-readable names to identifiers before mutations.
- Read the target asset before editing it.
- Ask for confirmation before destructive or broad updates.
- Preserve the exact rich-text and operation formats specified by the loaded guide.
- If the MCP server is unavailable or a listed guide cannot be loaded, state that the workflow is unavailable; do not substitute nonexistent local files.
