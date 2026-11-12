---
name: review-fastapi-deployment
description: Assess a stateless FastAPI container's source and configuration with
  Deployment Fixer and prepare an advisory ECS Express plan. Use before a cloud deployment
  review; this skill performs no builds, AWS actions or automatic fixes.
metadata:
  category: development
  source:
    repository: https://github.com/founder-sweep/contentsweep-deployment-fixer
    path: skills/review-fastapi-deployment
    ref: main
    commit: bc646b19e48054cfed636738c96296c7286fec5f
    license_path: LICENSE
  author: founder-sweep
---

# Review a FastAPI deployment

Start with free local analysis when source should stay on the machine. Choose hosted assessment when the user wants a saved hosted plan and authorizes the upload. Skill installation does not install the engine or connect MCP.

Use the [official setup guide](https://mcp.contentsweep.ai/deployment-fixer/docs), [local wheel](https://mcp.contentsweep.ai/deployment-fixer/download) and [SHA256 manifest](https://mcp.contentsweep.ai/deployment-fixer/downloads/manifest.json). Verify the download and install in Python 3.12+. CLI: `deployfixer`; local stdio MCP: `deployfixer-mcp`, sole tool `plan_deployment_readonly`.

```sh
deployfixer path/to/project --format json
```

Review file/line findings, application scope, start command, port, health-route evidence, configuration gaps and prerequisites. A statically found health route is not runtime readiness. Treat stateful, multi-service, invalid and unresolved applications as outside the hosted supported envelope. Inspect coverage rather than treating a local plan as assurance that the hosted assessment will be supported.

For hosted use, read [the workflow](references/hosted-workflow.md) before uploading or reserving a credit. Keep source/config files selected and bounded; exclude credentials and private environment files.

Deliver the assessment verdict, evidence, unresolved gaps and advisory review checklist. A completed assessment with blocking findings still consumes one hosted plan. Suggested resource lists describe contemplated resources; nothing has been created. Infrastructure cost is unquoted. No code imports, builds, image pulls, cloud credentials, automatic fixes, AWS execution or rollback occur through this product. The user's instruction to assess does not authorize later deployment or source edits.
