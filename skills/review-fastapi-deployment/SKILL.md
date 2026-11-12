---
name: review-fastapi-deployment
description: >-
  Assess a stateless FastAPI container's source and configuration with
  Deployment Fixer and prepare an advisory ECS Express plan. Use before a cloud
  deployment review; this skill performs no builds, AWS actions or automatic
  fixes.
metadata:
  category: development
  author: founder-sweep
  source:
    repository: 'https://github.com/founder-sweep/contentsweep-deployment-fixer'
    path: skills/review-fastapi-deployment
    license_path: LICENSE
    ref: main
    commit: f37a6edcf86ea4d2a4ce95fb4b6a3f6c0d8ab4ea
---

# Review a FastAPI deployment

Start with free local analysis when source should stay on the machine. Choose hosted assessment when the user wants a saved hosted plan and authorizes the upload. Skill installation does not install the engine or connect MCP.

Use the [official setup guide](https://mcp.contentsweep.ai/deployment-fixer/docs), [local wheel](https://mcp.contentsweep.ai/deployment-fixer/download) and [SHA256 manifest](https://mcp.contentsweep.ai/deployment-fixer/downloads/manifest.json). This reviewed skill pins version `1.0.0`, filename `contentsweep_deployment_fixer-1.0.0-py3-none-any.whl`, SHA256 `702e96cfa7c3a2daa5fb4cbee4feecf776653026e7c5739cd107bf78a7b102ae`. Verify the downloaded bytes against that literal digest and require the manifest's version, filename and SHA256 to agree before installing in a dedicated Python 3.12+ environment. Stop on any mismatch; do not adopt a replacement digest from the download origin without reviewing an updated skill revision. Configure the client with the installed executable's absolute path. CLI: `deployfixer`; local stdio MCP: `deployfixer-mcp`, sole tool `plan_deployment_readonly`.

```sh
deployfixer path/to/project --format json
```

Review file/line findings, application scope, start command, port, health-route evidence, configuration gaps and prerequisites. A statically found health route is not runtime readiness. Treat stateful, multi-service, invalid and unresolved applications as outside the hosted supported envelope. Inspect coverage rather than treating a local plan as assurance that the hosted assessment will be supported.

For hosted use, read [the workflow](references/hosted-workflow.md) before uploading or reserving a credit. Keep source/config files selected and bounded; exclude credentials and private environment files.

Deliver the assessment verdict, evidence, unresolved gaps and advisory review checklist. A completed assessment with blocking findings still consumes one hosted plan. Suggested resource lists describe contemplated resources; nothing has been created. Infrastructure cost is unquoted. No code imports, builds, image pulls, cloud credentials, automatic fixes, AWS execution or rollback occur through this product. The user's instruction to assess does not authorize later deployment or source edits.
