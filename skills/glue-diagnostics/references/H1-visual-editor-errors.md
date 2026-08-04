---
title: "H1 — Visual Editor Errors"
description: "Diagnose Glue Studio visual editor errors and configuration issues"
status: active
severity: MEDIUM
triggers:
  - "Glue Studio error"
  - "visual editor error"
  - "visual ETL error"
  - "node configuration error"
  - "visual job failed"
owner: devops-agent
objective: "Resolve Glue Studio visual editor errors that prevent job creation or execution"
context: "Glue Studio provides a visual interface for building ETL jobs. Visual editor errors include node configuration issues, incompatible node connections, missing required fields, unsupported data source configurations, and browser-related rendering issues. The visual editor generates PySpark code that may differ from hand-written scripts. Not all PySpark operations are available as visual nodes."
---

## Phase 1 — Triage

MUST:
- Identify the specific error in the Glue Studio console (node-level or job-level)
- Check node configurations for missing required fields
- Verify data source and target configurations are valid
- Check if the node connections form a valid DAG (no cycles, all inputs connected)

SHOULD:
- Review the generated script tab for code-level errors
- Verify IAM permissions for the Glue Studio user (glue:* and related permissions)
- Check if the Glue version supports the selected transforms
- Verify Data Catalog tables referenced by source nodes exist

MAY:
- Clear browser cache and retry if the visual editor is unresponsive
- Check for Glue Studio service health in the AWS Health Dashboard
- Try recreating the job from scratch if the visual state is corrupted

## Phase 2 — Remediate

MUST:
- Fix the identified node configuration error
- Ensure all required fields are populated in each node
- Verify the job runs successfully after the fix

SHOULD:
- Use the script editor to fix issues not resolvable in the visual editor
- Add custom code transform nodes for unsupported operations
- Save job frequently to avoid losing visual editor state

MAY:
- Export the job script and maintain it as code for version control
- Use CloudFormation or Terraform for job definition management
- Document visual editor limitations for the team

## Common Issues

- symptoms: "Visual editor shows 'Invalid node configuration' error"
  diagnosis: "Required field missing in a transform node (e.g., join key not specified, mapping not defined)."
  resolution: "Click on the error node and fill in all required configuration fields."

- symptoms: "Visual editor cannot connect two nodes"
  diagnosis: "Incompatible schema between source and target nodes, or node type does not accept the connection."
  resolution: "Add an ApplyMapping or SelectFields node between incompatible nodes to align schemas."

- symptoms: "Visual editor loads but shows blank canvas"
  diagnosis: "Browser cache issue or job definition corrupted."
  resolution: "Clear browser cache. Try a different browser. If persistent, recreate the job."

## Output Format

```yaml
root_cause: "visual_editor_error — <specific_cause>"
evidence:
  - type: node_config
    content: "<node configuration and error message>"
  - type: job_definition
    content: "<visual job structure>"
severity: MEDIUM
mitigation:
  immediate: "Fix node configuration or use script editor"
  long_term: "Document limitations, use IaC for job management"
```


## Safety Ratings
```
safety_ratings:
  - "Check node configurations: GREEN — read-only inspection"
  - "Review generated script: GREEN — read-only code review"
  - "Fix node configuration: GREEN — visual editor change"
  - "Switch to script editor: YELLOW — disconnects from visual mode permanently"
  - "Recreate job: YELLOW — requires rebuilding the visual design"
```

## Escalation Conditions
- Job processes production data pipeline
- Visual editor errors blocking job creation
- Generated code not matching visual design
- Visual editor state corrupted requiring recreation
- Limitations requiring switch to script mode

## Data Sensitivity
```
data_sensitivity:
  classification: HIGH
  sensitive_fields:
    - "Job definition: ETL logic and data flow"
    - "Node configurations: data source and target details"
    - "Generated script: transformation code"
  handling: "Job definitions reveal data processing logic. Do not expose externally."
```

## Prohibited Actions
- NEVER suggest resetting job bookmarks without understanding reprocessing impact
- NEVER suggest deleting Data Catalog tables
- NEVER edit generated script directly if you want to keep visual mode
- NEVER delete a visual job without exporting the script first

## Phase 3 — Rollback
- If node configuration was changed: undo in the visual editor
- If job was switched to script mode: CANNOT revert to visual mode — recreate as visual job
- If job was recreated: restore from previous job definition if available

## Escalation Conditions

escalation_conditions:
  - "Remediation requires modifying IAM policies in a production account"
  - "Remediation requires disabling a security control even temporarily"
  - "Root cause cannot be identified after 3 hypothesis pivots"
  - "Blast radius affects more than one account or region"
  - "Issue involves potential data loss or exposure"

## Prohibited Actions

prohibited_actions:
  - "NEVER suggest disabling encryption for Glue jobs"
  - "NEVER suggest overly broad Glue service role"
  - "NEVER suggest public S3 access for data catalog"
