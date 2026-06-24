---
name: "adf-master"
description: "Azure Data Factory (ADF) CI/CD, deployment, and pipeline development. PROACTIVELY activate for: (1) ADF CI/CD setup (npm validation, ARM template export), (2) ADF ARM template deployment, (3) ADF npm build validation in CI, (4) PrePostDeploymentScript for trigger and resource cleanup, (5) ADF GitHub Actions workflows, (6) ADF Azure DevOps pipelines, (7) ADF Git integration (collaboration vs publish branch), (8) parameterizing linked services and datasets across environments, (9) ADF triggers (schedule, tumbling window, event), (10) deployment slots and blue-green for ADF. Provides: complete CI/CD YAML for GitHub Actions and Azure DevOps, PrePostDeploymentScript reference, parameterization patterns, and trigger management recipes."
metadata:
  category: data
  source:
    repository: "https://github.com/JosiahSiegel/claude-plugin-marketplace"
    path: "plugins/adf-master/skills/adf-master"
    license_path: "LICENSE"
---

# Azure Data Factory Master Knowledge Base

## Deprecated Features

### Apache Airflow Workflow Orchestration Manager - DEPRECATED

**Status:** Deprecated since early 2025. Available only for existing customers.
**Retirement Date:** Not yet announced, but no new deployments permitted.
**Impact:** New customers cannot provision Apache Airflow in Azure Data Factory.

**Deprecation Details:**
- Apache Airflow Workflow Orchestration Manager is deprecated with no retirement date set
- Only existing deployments can continue using this feature
- No new Airflow integrations can be created in ADF

**Migration Path:**
- **Recommended:** Migrate to Fabric Data Factory with native Airflow support
- **Alternative:** Use standalone Apache Airflow deployments (Azure Container Instances, AKS, or VM-based)
- **Alternative:** Migrate orchestration logic to native ADF pipelines with control flow activities

**Why Deprecated:**
- Microsoft focus shifted to Fabric Data Factory as the unified data integration platform
- Fabric provides modern orchestration capabilities superseding Airflow integration
- Limited adoption and maintenance burden for standalone Airflow feature in ADF

**Action Required:**
- If using Airflow in ADF: Migrate to Fabric Data Factory, standalone Airflow, or native ADF patterns
- For new projects: Do NOT use Airflow in ADF
- Monitor Microsoft announcements for official retirement timeline

**Reference:**
- Microsoft Roadmap: https://www.directionsonmicrosoft.com/roadmaps/ref/azure-data-factory-roadmap/

## Feature Updates (2025-2026)

### Microsoft Fabric Integration (GA)

**ADF Mounting in Fabric:**
- Bring existing ADF pipelines into Fabric workspaces without rebuilding
- Generally Available since June 2025
- Seamless integration enables hybrid ADF + Fabric workflows

**Cross-Workspace Pipeline Orchestration:**
- New **Invoke Pipeline** activity supports cross-platform calls
- Invoke pipelines across Fabric, Azure Data Factory, and Synapse
- Managed VNet support for secure cross-workspace communication

**Variable Libraries:**
- Environment-specific variables for CI/CD automation
- Automatic value substitution during workspace promotion
- Eliminates separate parameter files per environment

**Connector Enhancements:**
- ServiceNow V2 (V1 End of Support)
- Enhanced PostgreSQL and Snowflake connectors
- Native OneLake connectivity for zero-copy integration

### Node.js 20.x Requirement for CI/CD

**CRITICAL:** As of 2025, npm package `@microsoft/azure-data-factory-utilities` requires Node.js 20.x

**Breaking Change:**
- Older Node.js versions (14.x, 16.x, 18.x) may cause package incompatibility errors
- Update CI/CD pipelines to use Node.js 20.x or compatible versions

**GitHub Actions:**
```yaml
- name: Setup Node.js
  uses: actions/setup-node@v4
  with:
    node-version: '20.x'
```

**Azure DevOps:**
```yaml
- task: UseNode@1
  inputs:
    version: '20.x'
```

## Official Documentation Sources

### Primary Microsoft Learn Resources

**Main Documentation Hub:**
- URL: https://learn.microsoft.com/en-us/azure/data-factory/
- Last Updated: February 2025
- Coverage: Complete ADF documentation including tutorials, concepts, how-to guides, and reference materials
- Key Topics: Pipelines, datasets, triggers, linked services, data flows, integration runtimes, monitoring

**Introduction to Azure Data Factory:**
- URL: https://learn.microsoft.com/en-us/azure/data-factory/introduction
- Summary: Managed cloud service for complex hybrid ETL, ELT, and data integration projects
- Key Features: 90+ built-in connectors, serverless architecture, code-free UI, single-pane monitoring

### Context7 Library Documentation

**Library ID:** `/websites/learn_microsoft_en-us_azure_data-factory`
- Trust Score: 7.5
- Code Snippets: 10,839
- Topics: CI/CD, ARM templates, pipeline patterns, data flows, monitoring, troubleshooting

**How to Access:**
```text
Use Context7 MCP tool to fetch latest documentation:
mcp__context7__get-library-docs:
  - context7CompatibleLibraryID: /websites/learn_microsoft_en-us_azure_data-factory
  - topic: "CI/CD continuous integration deployment pipelines ARM templates"
  - tokens: 8000
```

## CI/CD Deployment

Detailed CI/CD coverage — ARM template generation, the `PrePostDeploymentScript.ps1` pattern (stop/start triggers around deploys, cleanup of removed resources), and complete GitHub Actions + Azure DevOps pipeline YAMLs — lives in `references/cicd-deployment.md`. Load that reference when wiring continuous deployment for an ADF instance or troubleshooting a deploy pipeline.

## Troubleshooting Resources

### Official Troubleshooting Guide

**URL:** https://learn.microsoft.com/en-us/azure/data-factory/ci-cd-github-troubleshoot-guide
**Last Updated:** January 2025

**Common Issues Covered:**
1. Template parameter validation errors
2. Integration Runtime type cannot be changed
3. ARM template size exceeds 4MB limit
4. Git connection problems
5. Authentication failures
6. Deployment errors

### Diagnostic Logs

**Enable Diagnostic Settings:**
```text
Azure Portal → Data Factory → Diagnostic settings → Add diagnostic setting
Send to: Log Analytics workspace

Logs to Enable:
- PipelineRuns
- TriggerRuns
- ActivityRuns
- SandboxPipelineRuns
- SandboxActivityRuns
```

**Kusto Queries for Troubleshooting:**

```kusto
// Failed pipeline runs in last 24 hours
ADFPipelineRun
| where Status == "Failed"
| where TimeGenerated > ago(24h)
| project TimeGenerated, PipelineName, RunId, Status, ErrorMessage, Parameters
| order by TimeGenerated desc

// Failed CI/CD deployments
ADFActivityRun
| where ActivityType == "ExecutePipeline"
| where Status == "Failed"
| where TimeGenerated > ago(7d)
| project TimeGenerated, PipelineName, ActivityName, ErrorCode, ErrorMessage
| order by TimeGenerated desc

// Performance analysis
ADFActivityRun
| where TimeGenerated > ago(7d)
| extend DurationMinutes = datetime_diff('minute', End, Start)
| summarize AvgDuration = avg(DurationMinutes) by ActivityType, ActivityName
| where AvgDuration > 10
| order by AvgDuration desc
```

### Common Error Patterns

**Error: "Template parameters are not valid"**
- Cause: Deleted triggers still referenced in parameters
- Solution: Regenerate ARM template or use PrePostDeploymentScript cleanup

**Error: "Updating property type is not supported"**
- Cause: Trying to change Integration Runtime type
- Solution: Delete and recreate IR (not in-place update)

**Error: "Operation timed out"**
- Cause: Network connectivity, large data volume, insufficient compute
- Solution: Increase timeout, optimize query, increase DIUs

**Error: "Authentication failed"**
- Cause: Service principal expired, missing permissions, wrong credentials
- Solution: Verify credentials, check role assignments, renew if expired

## Best Practices

### Repository Structure

**Recommended Folder Layout:**
```text
repository-root/
├── adf-resources/          # ADF JSON files (if using npm approach)
│   ├── dataset/
│   ├── pipeline/
│   ├── trigger/
│   ├── linkedService/
│   └── integrationRuntime/
├── .github/
│   └── workflows/          # GitHub Actions workflows
│       ├── adf-build.yml
│       └── adf-deploy.yml
├── azure-pipelines/        # Azure DevOps pipelines
│   ├── build.yml
│   └── release.yml
├── parameters/             # Environment-specific parameters
│   ├── ARMTemplateParametersForFactory.dev.json
│   ├── ARMTemplateParametersForFactory.test.json
│   └── ARMTemplateParametersForFactory.prod.json
├── package.json            # npm configuration
└── README.md
```

### Git Configuration

**Only Configure Git on Development ADF:**
- Development: Git-integrated for source control
- Test: CI/CD deployment only (no Git)
- Production: CI/CD deployment only (no Git)

**Rationale:** Prevents accidental manual changes in higher environments

### Multi-Environment Strategy

```text
Environment Flow:
Dev (Git) → Build → Test → Approval → Production
            ↓
        ARM Templates
```

**Parameter Management:**
- Separate parameter file per environment
- Store secrets in Azure Key Vault
- Reference Key Vault in parameter files
- Never commit secrets to source control

### Monitoring and Alerting

**Set up alerts for:**
- Build pipeline failures
- Deployment failures
- Pipeline run failures
- Performance degradation
- Cost anomalies

**Recommended Tools:**
- Azure Monitor (Metrics and Alerts)
- Log Analytics (Kusto queries)
- Application Insights (for custom logging)
- Azure Advisor (optimization recommendations)

## Additional Resources

### GitHub Repositories

**Official Azure Data Factory Samples:**
- URL: https://github.com/Azure/Azure-DataFactory
- Path: SamplesV2/ContinuousIntegrationAndDelivery/
- Contents: PrePostDeploymentScript.Ver2.ps1, example pipelines, documentation

**Community Examples:**
- Search GitHub for "azure-data-factory-cicd" for real-world examples
- Many organizations publish their CI/CD patterns as reference

### Community Support

**Microsoft Q&A:**
- URL: https://learn.microsoft.com/en-us/answers/tags/130/azure-data-factory
- Active community, Microsoft employees respond

**Stack Overflow:**
- Tag: `azure-data-factory`
- Large knowledge base of resolved issues

**Azure Status:**
- URL: https://status.azure.com
- Check for service outages and incidents

## When to Fetch Latest Information

**Situations requiring current documentation:**
1. npm package version updates
2. New ADF features or activities
3. Changes to ARM template schema
4. Updates to PrePostDeploymentScript
5. New GitHub Actions or Azure DevOps tasks
6. Breaking changes or deprecations

**How to Fetch:**
- Use WebFetch for Microsoft Learn articles
- Check npm for latest package version
- Use Context7 for comprehensive topic coverage
- Review Azure Data Factory GitHub for script updates

This knowledge base should be your starting point for all Azure Data Factory questions. Always verify critical information with the latest official documentation when making production decisions.

## Progressive Disclosure References

For detailed JSON schemas and complete reference materials, see:

- **Activity Types**: `references/activity-types.md` - Complete JSON schemas for all activity types (Copy, ForEach, IfCondition, Switch, Until, Lookup, ExecutePipeline, WebActivity, DatabricksJob, SetVariable, AppendVariable, Wait, Fail, GetMetadata)
- **Expression Functions**: `references/expression-functions.md` - Complete reference for all ADF expression functions (string, collection, logical, conversion, math, date/time, pipeline/activity references)
- **Linked Services**: `references/linked-services.md` - Complete JSON configurations for all connector types (Blob Storage, ADLS Gen2, Azure SQL, Synapse, Fabric Lakehouse/Warehouse, Databricks, Key Vault, REST, SFTP, Snowflake, PostgreSQL)
- **Triggers**: `references/triggers.md` - Complete JSON schemas for schedule, tumbling window, and event triggers
- **Datasets**: `references/datasets.md` - Complete JSON schemas for all dataset types with parameterization patterns

For machine learning and analytics patterns, see the dedicated skill:
- **ML & Analytics**: `adf-master:adf-ml-analytics` - Azure ML pipelines, batch endpoints, Azure AI Services, Databricks ML/MLflow, SQL-to-Storage archival, feature engineering with Data Flows
