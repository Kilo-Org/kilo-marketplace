---
title: "H2 — Job Generation Issues"
description: "Diagnose issues with Glue Studio generated code not matching visual design"
status: active
severity: MEDIUM
triggers:
  - "generated code wrong"
  - "script does not match visual"
  - "code generation error"
  - "visual to script mismatch"
  - "auto-generated script"
owner: devops-agent
objective: "Resolve discrepancies between Glue Studio visual design and generated job scripts"
context: "Glue Studio generates PySpark scripts from the visual DAG. Generated code may not match expectations due to transform ordering, implicit type conversions, join type defaults, or visual editor limitations. Editing the generated script directly switches the job to 'script mode' and disconnects it from the visual editor. Custom code nodes allow mixing visual and code approaches."
---

## Phase 1 — Triage

MUST:
- Compare the visual design with the generated script in the Script tab
- Identify the specific discrepancy (wrong transform order, missing operation, incorrect parameters)
- Check if the job is in visual mode or script mode
- Verify the generated code compiles and runs without syntax errors

SHOULD:
- Review the generated code for implicit defaults (e.g., join type defaults to inner)
- Check if custom code nodes are generating correct code
- Verify ApplyMapping transformations match expected column mappings
- Check for DynamicFrame vs DataFrame conversion issues in generated code

MAY:
- Compare generated code with a hand-written equivalent
- Check Glue Studio version for known code generation bugs
- Review AWS documentation for expected code generation behavior

## Phase 2 — Remediate

MUST:
- Fix the discrepancy either in the visual editor or by editing the script
- If editing the script, understand that the job switches to script mode permanently
- Verify the corrected job produces expected output

SHOULD:
- Use custom code transform nodes for operations not correctly generated
- Keep the job in visual mode when possible for maintainability
- Document any manual script modifications for the team

MAY:
- Maintain the job as a pure script if visual editor limitations are too restrictive
- Use version control for the job script
- Create reusable custom transform nodes for common patterns

## Common Issues

- symptoms: "Generated join uses wrong join type"
  diagnosis: "Visual editor defaults to inner join. The join type configuration may not be visible or was not changed."
  resolution: "Explicitly set the join type in the Join node configuration. Verify in the generated script."

- symptoms: "Generated code has wrong column order in output"
  diagnosis: "Visual editor does not guarantee column ordering. ApplyMapping may reorder columns."
  resolution: "Add a SelectFields node after the transformation to enforce column order."

- symptoms: "Editing script disconnected the visual editor"
  diagnosis: "Manual script edits switch the job from visual mode to script mode permanently."
  resolution: "Create a new visual job and recreate the design. Use custom code nodes instead of editing the generated script directly."

## Output Format

```yaml
root_cause: "job_generation — <specific_cause>"
evidence:
  - type: visual_design
    content: "<visual DAG description>"
  - type: generated_script
    content: "<relevant generated code section>"
severity: MEDIUM
mitigation:
  immediate: "Fix in visual editor or switch to script mode"
  long_term: "Use custom code nodes, maintain scripts in version control"
```


## Safety Ratings
```
safety_ratings:
  - "Compare visual design with generated script: GREEN — read-only analysis"
  - "Fix in visual editor: GREEN — visual editor change"
  - "Add custom code transform node: GREEN — extends visual design"
  - "Edit generated script directly: YELLOW — permanently switches to script mode"
```

## Escalation Conditions
- Job processes production data pipeline
- Generated code producing incorrect output
- Visual editor limitations requiring script mode
- Code generation bugs requiring workarounds
- Join type or column ordering issues in generated code

## Data Sensitivity
```
data_sensitivity:
  classification: HIGH
  sensitive_fields:
    - "Generated script: ETL transformation logic"
    - "Visual DAG: data flow design"
    - "Node parameters: data source and target details"
  handling: "Generated scripts reveal data processing logic. Do not expose externally."
```

## Prohibited Actions
- NEVER suggest resetting job bookmarks without understanding reprocessing impact
- NEVER suggest deleting Data Catalog tables
- NEVER edit generated script if visual mode needs to be preserved
- NEVER assume generated code is correct without verification

## Phase 3 — Rollback
- If visual design was changed: undo changes in the visual editor
- If custom code node was added: remove the node if it causes errors
- If script was edited directly: CANNOT revert to visual mode — recreate as visual job
- If job was switched to script mode: maintain the script version in source control

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
