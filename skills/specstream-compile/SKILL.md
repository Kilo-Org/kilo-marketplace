---
name: specstream-compile
description: >-
  Read a plain-English SpecStream request back to the person before anything
  runs. No price, no work.
license: MIT
metadata:
  category: search
  author: SpecStream
  source:
    repository: 'https://github.com/specstream/specstream-tools'
    path: integrations/kilo/skills/specstream-compile
    ref: main
    commit: 899bb63328dd72ba7613f66c7dc36dd59d1bf188
---

# Read the request

SpecStream is the live web data engine for teams and agents. Use the configured MCP server at `https://api.specstream.ai/mcp`.

Use `compile` to read the person's request. Say back what it found: the kind of thing, the conditions, the details to bring back and the quantity. Separate the conditions that must hold from the details that are nice to have. Use `edit_spec` for a deliberate change. Never drop a hard condition quietly, and never treat missing evidence as a no. Reading a request does not start any work.

Suggest requests that work well: local businesses with ratings, companies from registries, grants, tenders, clinical trials, papers, datasets, regulations, vulnerabilities, apps, repositories, packages, podcasts and books. Companies that use a tool, funding and new-executive signals, US nonprofits and UK financial firms by FCA status also work. If someone asks for people by job title, say that results may be few. `list_request_templates` returns requests that already work for each kind.

The same saved request can be revised, branched, compared and shared, in the workspace or through this agent. Never ask for an API key in chat. Use the connector's own sign-in.
