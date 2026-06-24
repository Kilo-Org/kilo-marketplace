# ADF CI/CD Deployment (ARM, PrePostDeploymentScript, GitHub Actions, Azure DevOps)

Deep dive into ADF deployment: ARM template generation, the `PrePostDeploymentScript.ps1` pattern (stop/start triggers around deploys, cleanup of removed resources), and complete GitHub Actions + Azure DevOps pipeline YAMLs. SKILL.md keeps deprecated features, 2025-2026 updates, doc sources, troubleshooting, and best practices; this reference holds the deployment material.

## CI/CD Deployment Methods

### Modern Automated Approach (Recommended)

**npm Package:** `@microsoft/azure-data-factory-utilities`
- **Latest Version:** 1.0.3+ (check npm for current version)
- **npm URL:** https://www.npmjs.com/package/@microsoft/azure-data-factory-utilities
- **Node.js Requirement:** Version 20.x or compatible

**Key Features:**
- Validates ADF resources independently of service
- Generates ARM templates programmatically
- Enables true CI/CD without manual publish button
- Supports preview mode for selective trigger management

**package.json Configuration:**
```json
{
  "scripts": {
    "build": "node node_modules/@microsoft/azure-data-factory-utilities/lib/index",
    "build-preview": "node node_modules/@microsoft/azure-data-factory-utilities/lib/index --preview"
  },
  "dependencies": {
    "@microsoft/azure-data-factory-utilities": "^1.0.3"
  }
}
```

**Commands:**
```bash
# Validate resources
npm run build validate <rootFolder> <factoryId>

# Generate ARM templates
npm run build export <rootFolder> <factoryId> [outputFolder]

# Preview mode (only stop/start modified triggers)
npm run build-preview export <rootFolder> <factoryId> [outputFolder]
```

**Official Documentation:**
- URL: https://learn.microsoft.com/en-us/azure/data-factory/continuous-integration-delivery-improvements
- Last Updated: January 2025
- Topics: Setup, configuration, build commands, CI/CD integration

### Traditional Manual Approach (Legacy)

**Method:** Git integration + Publish button

**Process:**
1. Configure Git integration in ADF UI (Dev environment only)
2. Make changes in ADF Studio
3. Click "Publish" button to generate ARM templates
4. Templates saved to `adf_publish` branch
5. Release pipelines deploy from `adf_publish` branch

**When to Use:**
- Migrating from existing setup
- No build pipeline infrastructure
- Simple deployments without validation

**Limitations:**
- Requires manual publish action
- No validation until publish
- Not true CI/CD (manual step required)
- Can't validate on pull requests

**Migration Path:** Modern approach recommended for new implementations

## ARM Template Deployment

### PowerShell Deployment

**Primary Command:** `New-AzResourceGroupDeployment`

**Syntax:**
```powershell
New-AzResourceGroupDeployment `
  -ResourceGroupName "<resource-group-name>" `
  -TemplateFile "ARMTemplateForFactory.json" `
  -TemplateParameterFile "ARMTemplateParametersForFactory.<environment>.json" `
  -factoryName "<factory-name>" `
  -Mode Incremental `
  -Verbose
```

**Validation:**
```powershell
Test-AzResourceGroupDeployment `
  -ResourceGroupName "<resource-group-name>" `
  -TemplateFile "ARMTemplateForFactory.json" `
  -TemplateParameterFile "ARMTemplateParametersForFactory.<environment>.json" `
  -factoryName "<factory-name>"
```

**What-If Analysis:**
```powershell
New-AzResourceGroupDeployment `
  -ResourceGroupName "<resource-group-name>" `
  -TemplateFile "ARMTemplateForFactory.json" `
  -TemplateParameterFile "ARMTemplateParametersForFactory.<environment>.json" `
  -factoryName "<factory-name>" `
  -WhatIf
```

### Azure CLI Deployment

**Primary Command:** `az deployment group create`

**Syntax:**
```bash
az deployment group create \
  --resource-group <resource-group-name> \
  --template-file ARMTemplateForFactory.json \
  --parameters ARMTemplateParametersForFactory.<environment>.json \
  --parameters factoryName=<factory-name> \
  --mode Incremental
```

**Validation:**
```bash
az deployment group validate \
  --resource-group <resource-group-name> \
  --template-file ARMTemplateForFactory.json \
  --parameters ARMTemplateParametersForFactory.<environment>.json \
  --parameters factoryName=<factory-name>
```

**What-If Analysis:**
```bash
az deployment group what-if \
  --resource-group <resource-group-name> \
  --template-file ARMTemplateForFactory.json \
  --parameters ARMTemplateParametersForFactory.<environment>.json \
  --parameters factoryName=<factory-name>
```

## PrePostDeploymentScript

### Current Version: Ver2

**Location:** https://github.com/Azure/Azure-DataFactory/blob/main/SamplesV2/ContinuousIntegrationAndDelivery/PrePostDeploymentScript.Ver2.ps1

**Key Improvement in Ver2:**
- Turns off/on ONLY triggers that have been modified
- Ver1 stopped/started ALL triggers (slower, more disruptive)
- Compares trigger payloads to determine changes

**Download Command:**
```bash
# Linux/macOS/Git Bash
curl -o PrePostDeploymentScript.Ver2.ps1 https://raw.githubusercontent.com/Azure/Azure-DataFactory/main/SamplesV2/ContinuousIntegrationAndDelivery/PrePostDeploymentScript.Ver2.ps1

# PowerShell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Azure/Azure-DataFactory/main/SamplesV2/ContinuousIntegrationAndDelivery/PrePostDeploymentScript.Ver2.ps1" -OutFile "PrePostDeploymentScript.Ver2.ps1"
```

### Parameters

**Pre-Deployment (Stop Triggers):**
```powershell
./PrePostDeploymentScript.Ver2.ps1 `
  -armTemplate "<path-to-ARMTemplateForFactory.json>" `
  -ResourceGroupName "<resource-group-name>" `
  -DataFactoryName "<factory-name>" `
  -predeployment $true `
  -deleteDeployment $false
```

**Post-Deployment (Start Triggers & Cleanup):**
```powershell
./PrePostDeploymentScript.Ver2.ps1 `
  -armTemplate "<path-to-ARMTemplateForFactory.json>" `
  -ResourceGroupName "<resource-group-name>" `
  -DataFactoryName "<factory-name>" `
  -predeployment $false `
  -deleteDeployment $true
```

### PowerShell Requirements

**Version:** PowerShell Core (7.0+) recommended
- Azure DevOps: Use `pwsh: true` in AzurePowerShell@5 task
- Locally: Use `pwsh` command, not `powershell`

**Modules Required:**
- Az.DataFactory
- Az.Resources

**Official Documentation:**
- URL: https://learn.microsoft.com/en-us/azure/data-factory/continuous-integration-delivery-sample-script
- Last Updated: January 2025

## GitHub Actions CI/CD

### Official Resources

**Medium Article (Recent 2025):**
- URL: https://medium.com/microsoftazure/azure-data-factory-build-and-deploy-with-new-ci-cd-flow-using-github-actions-cd46c95054e0
- Author: Jared Zagelbaum (Microsoft Azure)
- Topics: Modern CI/CD flow, npm package usage, GitHub Actions setup

**Microsoft Community Hub:**
- URL: https://techcommunity.microsoft.com/blog/fasttrackforazureblog/azure-data-factory-cicd-with-github-actions/3768493
- Topics: End-to-end GitHub Actions setup, workload identity federation

**Community Blog (February 2025):**
- URL: https://linusdata.blog/2025/03/14/automating-azure-data-factory-deployments-with-github-actions/
- Topics: Practical implementation guide, troubleshooting tips

### Key GitHub Actions

**Essential Actions:**
- `actions/checkout@v4` - Checkout repository
- `actions/setup-node@v4` - Setup Node.js
- `actions/upload-artifact@v4` - Publish ARM templates
- `actions/download-artifact@v4` - Download ARM templates in deploy workflow
- `azure/login@v2` - Authenticate to Azure
- `azure/arm-deploy@v2` - Deploy ARM templates
- `azure/powershell@v2` - Run PrePostDeploymentScript

### Authentication Methods

**Service Principal (JSON credentials):**
```json
{
  "clientId": "<GUID>",
  "clientSecret": "<STRING>",
  "subscriptionId": "<GUID>",
  "tenantId": "<GUID>"
}
```
Store in GitHub secret: `AZURE_CREDENTIALS`

**Workload Identity Federation (More secure):**
- No secrets stored
- Uses OIDC (OpenID Connect)
- Recommended for production
- Setup: https://learn.microsoft.com/en-us/azure/developer/github/connect-from-azure

## Azure DevOps CI/CD

### Official Resources

**Microsoft Learn:**
- URL: https://learn.microsoft.com/en-us/azure/data-factory/continuous-integration-delivery-automate-azure-pipelines
- Topics: Build pipeline, release pipeline, service connections, variable groups

**Community Guides:**
- Adam Marczak Blog: https://marczak.io/posts/2023/02/quick-cicd-for-data-factory/
- Topics: Quick setup, best practices, folder structure

**Towards Data Science:**
- URL: https://towardsdatascience.com/azure-data-factory-ci-cd-made-simple-building-and-deploying-your-arm-templates-with-azure-devops-30c30595afa5
- Topics: ARM template build and deployment workflow

### Key Azure DevOps Tasks

**Build Pipeline Tasks:**
- `UseNode@1` - Install Node.js
- `Npm@1` - Install packages, run build commands
- `PublishPipelineArtifact@1` - Publish ARM templates

**Release Pipeline Tasks:**
- `DownloadPipelineArtifact@2` - Download ARM templates
- `AzurePowerShell@5` - Run PrePostDeploymentScript
- `AzureResourceManagerTemplateDeployment@3` - Deploy ARM template

### Service Connection Requirements

**Permissions Needed:**
- Data Factory Contributor (on all Data Factories)
- Contributor (on Resource Groups)
- Key Vault access policies (if using secrets)

**Configuration:**
- Project Settings → Service connections → New service connection
- Type: Azure Resource Manager
- Authentication: Service Principal (recommended) or Managed Identity
