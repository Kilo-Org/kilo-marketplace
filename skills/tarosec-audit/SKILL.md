---
name: tarosec-audit
description: >-
  Audit application source, authentication and authorization, dependencies,
  secrets, CI/CD pipelines, MCP tools and Agent Skills for security weaknesses,
  and verify remediation of earlier findings. Use for code security reviews,
  dependency and supply-chain triage, agent/skill/MCP security audits, and fix
  verification. Not for live target testing (tarosec-red), log investigation
  (tarosec-blue) or general code review without a security question.
license: MIT
metadata:
  suite: tarosec
  version: 0.1.0
  category: security
  source:
    repository: 'https://github.com/refactorroom/tarosec'
    path: skills/tarosec-audit
    ref: v0.1.0
    commit: e0f05dde5cb8bf93dc5d149ee779cf85a83b679b
---

# Tarosec Audit — Security Auditor

Bounded, read-only security audit of code and configuration the user owns or may
assess. Read [authorization](references/shared/authorization.md),
[evidence handling](references/shared/evidence-handling.md) and
[standards](references/shared/security-standards.md).

## Modes

| Mode | Outcome |
| --- | --- |
| `quick` (default) | Triage exposed/privileged paths, secrets, dangerous config; list deferred coverage. |
| `deep` | Trace all applicable boundaries in scope; enumerate uninspected areas. |
| `dependencies` | Triage dependency/advisory reports against resolved versions and paths. See [dependencies](references/dependencies.md). |
| `agents` | Skills, prompts, hooks, MCP/tool definitions and their permission paths. See [agents](references/agents.md). |
| `verify` | Re-check supplied findings against current source; keep original IDs. |

## Workflow

1. **Map exposure.** Entry points, attacker-controlled input, identities,
   privilege checks, sensitive assets, trust boundaries. Don't assume a web app.
2. **Trace candidates to the sink.** Follow input to the dangerous operation and
   inspect the effective guard (binding, allowlist, ownership/tenant check,
   encoding). A dangerous API name or scanner hit alone is not a vulnerability.
   Passing tests are not proof of a guard: check what the tests actually assert.
3. **Validate safely.** Use a static trace or review a supplied regression result. Never run
   untrusted install scripts, hooks or audited skills to see if they're safe;
   never test a found credential against its provider.
4. **Rank and reconcile.** One root cause = one finding. Severity (with rationale)
   and confidence are separate; no fabricated CVSS. Map CWE/ASVS 5.0 only when the
   requirement is verified.
5. **Report coverage honestly.** Inspected, not applicable (with evidence), or
   unverified for each requested area. Failed or unrun scanners are Not Run.

## Output

Scope and revision, short threat model, ranked findings (location, attacker
prerequisite and causal path, impact, evidence, controls considered, fix,
regression check), checks actually run, coverage limits. Redact secrets by type
and location. Optional JSON uses `assets/schemas/finding.schema.json` with
`producer: tarosec-audit`. Read-only by default: source fixes, scanner installs,
uploads, commits and pushes need explicit authorization. `tarosec-red` can reuse
the finding ID when checking supplied assessment evidence.
