---
name: "powerbi-documentation"
description: "Create standardized documentation for Power BI semantic models and reports. Use when the user requests documentation for a Power BI project, semantic model, or report (e.g., \"document this model\", \"create documentation for this Power BI project\", \"generate documentation\"). This skill works with the powerbi-modeling-mcp server to extract model metadata and generate professional Word documents."
metadata:
  category: data
  source:
    repository: "https://github.com/MaartenKesters/powerbi-mcp-documentation"
    path: "powerbi-mcp-documentation"
    license_path: "LICENSE"
---

# Power BI Documentation Skill

Generate comprehensive, standardized documentation for Power BI semantic models using an interactive workflow.

## Prerequisites

Before starting documentation, ensure:
1. The powerbi-modeling-mcp server is connected and available
2. Connection to the target semantic model is established (Power BI Desktop, Fabric workspace, or PBIP folder)

## Interactive Documentation Workflow

**CRITICAL:** This skill uses a conversational approach. The agent MUST ask questions one at a time and wait for user responses before proceeding. Do NOT generate the document until all questions are answered. All questions use numbered options (1/2/3/...) for consistency — never use Yes/No style answers.

### Phase 1: Connect and Gather Metadata

Before asking any questions, the agent should:

1. **Connect to the semantic model** using `connection_operations`
2. **Gather basic model information** using `model_operations`:
   - Model name
   - Table count (and table names for classification)
   - Measure count (including display folders)
   - Relationship count
   - File name (for document title)
   - Last modified date
3. **Check for calculation groups** using `calculation_group_operations` (ListGroups)
4. **Classify tables** by analyzing naming conventions and structure:
   - Fact tables (e.g., `fact_*`, `fct_*`, or tables with numeric measures and foreign keys)
   - Dimension tables (e.g., `dim_*`, `d_*`, or lookup/reference tables)
   - Parameter tables (e.g., `para_*`, `param_*`, or tables with What-If parameters)
   - Bridge/mapping tables
   - Date tables
   - Calculated tables
   - Other/Utility tables

This information is needed to ask informed questions and provide sensible defaults.

### Phase 2: Configure the document

Ask configuration questions one at a time and wait for each response. Use the preset or manual question sequence in [documentation-specification.md](references/documentation-specification.md#phase-2-interactive-configuration). Do not generate output until the configuration is complete.

### Phase 3: Generate and validate

1. Read only the selected section specifications in [documentation-specification.md](references/documentation-specification.md#phase-3-generate-documentation).
2. Extract the required model metadata with the narrowest available Power BI MCP operations.
3. Generate the Word document and any requested Mermaid diagram files.
4. Check that selected sections, names, counts, relationships, calculations, and sensitive-source redactions match the configuration.
5. Return links or paths for every generated output file.

## Safety and Quality

- Treat model metadata and provided business context as potentially sensitive; do not expose credentials or connection secrets.
- Do not invent table purposes, measure semantics, relationships, or business definitions. Mark missing descriptions as inferred or unknown.
- For large models, batch metadata retrieval and use the large-model rules in the detailed specification.
- Preserve DAX, M, table, column, and measure names exactly as defined in the model.

## Reference Navigation

Read [documentation-specification.md](references/documentation-specification.md) selectively for:

- interactive questions and preset templates
- document section templates and model diagrams
- MCP operation mapping
- Word visual style and formatting requirements
- edge cases, question flow, and output file conventions
