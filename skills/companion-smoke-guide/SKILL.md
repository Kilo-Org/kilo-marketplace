---
name: companion-smoke-guide
description: >-
  Verify the harmless Companion Smoke Test MCP connection and report its status
  without changing any external state.
license: MIT
metadata:
  category: development
  source:
    repository: 'https://github.com/marius-kilocode/kilo-companion-smoke-test'
    path: skills/companion-smoke-guide
    ref: main
    commit: 15029cb782446d2b5bc98cf0539cc03febc28162
---

# Companion Smoke Guide

Use this skill with the Companion Smoke Test MCP server.

1. Confirm the user wants to check the smoke-test server connection.
2. Call the server's read-only echo tool with a short acknowledgement string.
3. Report the returned text exactly as received.
4. Do not write, delete, or change any external state. This server is read-only.

If the tool is unavailable, report that the connection could not be verified instead of guessing.
