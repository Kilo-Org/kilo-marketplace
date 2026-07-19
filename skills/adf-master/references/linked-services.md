# ADF Linked Services - Complete JSON Reference

## Azure Blob Storage

### Managed Identity (Recommended)
```json
{
  "name": "LS_AzureBlobStorage_MI",
  "type": "Microsoft.DataFactory/factories/linkedservices",
  "properties": {
    "type": "AzureBlobStorage",
    "typeProperties": {
      "serviceEndpoint": "https://mystorageaccount.blob.core.windows.net",
      "accountKind": "StorageV2"
    },
    "connectVia": {
      "referenceName": "AutoResolveIntegrationRuntime",
      "type": "IntegrationRuntimeReference"
    }
  }
}
```

**CRITICAL:** `accountKind` is REQUIRED for Managed Identity. Valid values: `StorageV2`, `BlobStorage`, `BlockBlobStorage`

### Service Principal
```json
{
  "name": "LS_AzureBlobStorage_SP",
  "properties": {
    "type": "AzureBlobStorage",
    "typeProperties": {
      "serviceEndpoint": "https://mystorageaccount.blob.core.windows.net",
      "accountKind": "StorageV2",
      "servicePrincipalId": "<app-id>",
      "servicePrincipalKey": {
        "type": "AzureKeyVaultSecret",
        "store": {
          "referenceName": "LS_KeyVault",
          "type": "LinkedServiceReference"
        },
        "secretName": "storage-sp-key"
      },
      "tenant": "<tenant-id>"
    }
  }
}
```

### Connection String
```json
{
  "name": "LS_AzureBlobStorage_CS",
  "properties": {
    "type": "AzureBlobStorage",
    "typeProperties": {
      "connectionString": {
        "type": "AzureKeyVaultSecret",
        "store": {
          "referenceName": "LS_KeyVault",
          "type": "LinkedServiceReference"
        },
        "secretName": "blob-connection-string"
      }
    }
  }
}
```

### SAS URI
```json
{
  "name": "LS_AzureBlobStorage_SAS",
  "properties": {
    "type": "AzureBlobStorage",
    "typeProperties": {
      "sasUri": {
        "type": "AzureKeyVaultSecret",
        "store": { "referenceName": "LS_KeyVault", "type": "LinkedServiceReference" },
        "secretName": "blob-sas-uri"
      }
    }
  }
}
```

---

## Azure Data Lake Storage Gen2

### Managed Identity
```json
{
  "name": "LS_ADLS_MI",
  "properties": {
    "type": "AzureBlobFS",
    "typeProperties": {
      "url": "https://mydatalake.dfs.core.windows.net"
    }
  }
}
```

### Service Principal
```json
{
  "name": "LS_ADLS_SP",
  "properties": {
    "type": "AzureBlobFS",
    "typeProperties": {
      "url": "https://mydatalake.dfs.core.windows.net",
      "servicePrincipalId": "<app-id>",
      "servicePrincipalKey": {
        "type": "AzureKeyVaultSecret",
        "store": { "referenceName": "LS_KeyVault", "type": "LinkedServiceReference" },
        "secretName": "adls-sp-key"
      },
      "tenant": "<tenant-id>"
    }
  }
}
```

---

## Azure SQL Database

### Managed Identity (Recommended)
```json
{
  "name": "LS_AzureSql_MI",
  "properties": {
    "type": "AzureSqlDatabase",
    "typeProperties": {
      "server": "myserver.database.windows.net",
      "database": "mydb"
    }
  }
}
```

**Required SQL Setup:**
```sql
CREATE USER [datafactory-name] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [datafactory-name];
ALTER ROLE db_datawriter ADD MEMBER [datafactory-name];
```

### Connection String with Key Vault
```json
{
  "name": "LS_AzureSql_CS",
  "properties": {
    "type": "AzureSqlDatabase",
    "typeProperties": {
      "connectionString": {
        "type": "AzureKeyVaultSecret",
        "store": { "referenceName": "LS_KeyVault", "type": "LinkedServiceReference" },
        "secretName": "sql-connection-string"
      }
    }
  }
}
```

### SQL Authentication
```json
{
  "name": "LS_AzureSql_Auth",
  "properties": {
    "type": "AzureSqlDatabase",
    "typeProperties": {
      "server": "myserver.database.windows.net",
      "database": "mydb",
      "userName": "sqladmin",
      "password": {
        "type": "AzureKeyVaultSecret",
        "store": { "referenceName": "LS_KeyVault", "type": "LinkedServiceReference" },
        "secretName": "sql-password"
      }
    }
  }
}
```

---

## Azure Synapse Analytics

### Managed Identity
```json
{
  "name": "LS_Synapse_MI",
  "properties": {
    "type": "AzureSqlDW",
    "typeProperties": {
      "server": "mysynapse.sql.azuresynapse.net",
      "database": "mypool"
    }
  }
}
```

---

## Microsoft Fabric Lakehouse

```json
{
  "name": "LS_FabricLakehouse",
  "properties": {
    "type": "Lakehouse",
    "typeProperties": {
      "workspaceId": "12345678-1234-1234-1234-123456789abc",
      "artifactId": "87654321-4321-4321-4321-cba987654321"
    }
  }
}
```

With Service Principal:
```json
{
  "name": "LS_FabricLakehouse_SP",
  "properties": {
    "type": "Lakehouse",
    "typeProperties": {
      "workspaceId": "12345678-1234-1234-1234-123456789abc",
      "artifactId": "87654321-4321-4321-4321-cba987654321",
      "servicePrincipalId": "<app-id>",
      "servicePrincipalKey": {
        "type": "AzureKeyVaultSecret",
        "store": { "referenceName": "LS_KeyVault", "type": "LinkedServiceReference" },
        "secretName": "fabric-sp-key"
      },
      "tenant": "<tenant-id>"
    }
  }
}
```

---

## Microsoft Fabric Warehouse

### Managed Identity
```json
{
  "name": "LS_FabricWarehouse_MI",
  "properties": {
    "type": "Warehouse",
    "typeProperties": {
      "endpoint": "myworkspace.datawarehouse.fabric.microsoft.com",
      "warehouse": "MyWarehouse",
      "authenticationType": "SystemAssignedManagedIdentity"
    }
  }
}
```

### Service Principal
```json
{
  "name": "LS_FabricWarehouse_SP",
  "properties": {
    "type": "Warehouse",
    "typeProperties": {
      "endpoint": "myworkspace.datawarehouse.fabric.microsoft.com",
      "warehouse": "MyWarehouse",
      "authenticationType": "ServicePrincipal",
      "servicePrincipalId": "<app-id>",
      "servicePrincipalKey": {
        "type": "AzureKeyVaultSecret",
        "store": { "referenceName": "LS_KeyVault", "type": "LinkedServiceReference" },
        "secretName": "fabric-warehouse-key"
      },
      "tenant": "<tenant-id>"
    }
  }
}
```

---

## Azure Databricks

### Managed Identity (Serverless)
```json
{
  "name": "LS_Databricks_MI",
  "properties": {
    "type": "AzureDatabricks",
    "typeProperties": {
      "domain": "https://adb-1234567890123456.7.azuredatabricks.net",
      "authentication": "MSI"
    }
  }
}
```

### Access Token
```json
{
  "name": "LS_Databricks_Token",
  "properties": {
    "type": "AzureDatabricks",
    "typeProperties": {
      "domain": "https://adb-1234567890123456.7.azuredatabricks.net",
      "accessToken": {
        "type": "AzureKeyVaultSecret",
        "store": { "referenceName": "LS_KeyVault", "type": "LinkedServiceReference" },
        "secretName": "databricks-token"
      }
    }
  }
}
```

---

## Azure Key Vault

```json
{
  "name": "LS_KeyVault",
  "properties": {
    "type": "AzureKeyVault",
    "typeProperties": {
      "baseUrl": "https://mykeyvault.vault.azure.net"
    }
  }
}
```

**Required Permission:**
ADF managed identity needs `Get` permission on secrets.

---

## REST API

### Anonymous
```json
{
  "name": "LS_REST_Anonymous",
  "properties": {
    "type": "RestService",
    "typeProperties": {
      "url": "https://api.example.com",
      "authenticationType": "Anonymous"
    }
  }
}
```

### Basic Authentication
```json
{
  "name": "LS_REST_Basic",
  "properties": {
    "type": "RestService",
    "typeProperties": {
      "url": "https://api.example.com",
      "authenticationType": "Basic",
      "userName": "apiuser",
      "password": {
        "type": "AzureKeyVaultSecret",
        "store": { "referenceName": "LS_KeyVault", "type": "LinkedServiceReference" },
        "secretName": "api-password"
      }
    }
  }
}
```

### OAuth2 Client Credentials
```json
{
  "name": "LS_REST_OAuth",
  "properties": {
    "type": "RestService",
    "typeProperties": {
      "url": "https://api.example.com",
      "authenticationType": "OAuth2ClientCredential",
      "tokenEndpoint": "https://login.microsoftonline.com/<tenant>/oauth2/v2.0/token",
      "clientId": "<client-id>",
      "clientSecret": {
        "type": "AzureKeyVaultSecret",
        "store": { "referenceName": "LS_KeyVault", "type": "LinkedServiceReference" },
        "secretName": "oauth-client-secret"
      },
      "scope": "https://api.example.com/.default",
      "resource": "https://api.example.com"
    }
  }
}
```

### Managed Identity
```json
{
  "name": "LS_REST_MI",
  "properties": {
    "type": "RestService",
    "typeProperties": {
      "url": "https://management.azure.com",
      "authenticationType": "ManagedServiceIdentity",
      "aadResourceId": "https://management.azure.com/"
    }
  }
}
```

---

## SFTP

### Password
```json
{
  "name": "LS_SFTP_Password",
  "properties": {
    "type": "Sftp",
    "typeProperties": {
      "host": "sftp.example.com",
      "port": 22,
      "skipHostKeyValidation": false,
      "hostKeyFingerprint": "ssh-rsa 2048 xx:xx:xx...",
      "authenticationType": "Basic",
      "userName": "sftpuser",
      "password": {
        "type": "AzureKeyVaultSecret",
        "store": { "referenceName": "LS_KeyVault", "type": "LinkedServiceReference" },
        "secretName": "sftp-password"
      }
    },
    "connectVia": {
      "referenceName": "SelfHostedIR",
      "type": "IntegrationRuntimeReference"
    }
  }
}
```

### SSH Key
```json
{
  "name": "LS_SFTP_Key",
  "properties": {
    "type": "Sftp",
    "typeProperties": {
      "host": "sftp.example.com",
      "port": 22,
      "authenticationType": "SshPublicKey",
      "userName": "sftpuser",
      "privateKeyPath": "/home/user/.ssh/id_rsa",
      "passPhrase": {
        "type": "AzureKeyVaultSecret",
        "store": { "referenceName": "LS_KeyVault", "type": "LinkedServiceReference" },
        "secretName": "ssh-passphrase"
      }
    }
  }
}
```

---

## ServiceNow V2

```json
{
  "name": "LS_ServiceNowV2",
  "properties": {
    "type": "ServiceNowV2",
    "typeProperties": {
      "endpoint": "https://dev12345.service-now.com",
      "authenticationType": "OAuth2",
      "clientId": "<client-id>",
      "clientSecret": {
        "type": "AzureKeyVaultSecret",
        "store": { "referenceName": "LS_KeyVault", "type": "LinkedServiceReference" },
        "secretName": "servicenow-client-secret"
      },
      "username": "service-account@company.com",
      "password": {
        "type": "AzureKeyVaultSecret",
        "store": { "referenceName": "LS_KeyVault", "type": "LinkedServiceReference" },
        "secretName": "servicenow-password"
      },
      "grantType": "password"
    }
  }
}
```

---

## Snowflake

### Key Pair Authentication
```json
{
  "name": "LS_Snowflake",
  "properties": {
    "type": "Snowflake",
    "typeProperties": {
      "connectionString": "jdbc:snowflake://account.snowflakecomputing.com",
      "database": "mydb",
      "warehouse": "compute_wh",
      "authenticationType": "KeyPair",
      "user": "myuser",
      "privateKey": {
        "type": "AzureKeyVaultSecret",
        "store": { "referenceName": "LS_KeyVault", "type": "LinkedServiceReference" },
        "secretName": "snowflake-private-key"
      },
      "privateKeyPassphrase": {
        "type": "AzureKeyVaultSecret",
        "store": { "referenceName": "LS_KeyVault", "type": "LinkedServiceReference" },
        "secretName": "snowflake-passphrase"
      }
    }
  }
}
```

---

## PostgreSQL

```json
{
  "name": "LS_PostgreSQL",
  "properties": {
    "type": "PostgreSql",
    "typeProperties": {
      "connectionString": "host=myserver.postgres.database.azure.com;port=5432;database=mydb;uid=myadmin",
      "password": {
        "type": "AzureKeyVaultSecret",
        "store": { "referenceName": "LS_KeyVault", "type": "LinkedServiceReference" },
        "secretName": "postgres-password"
      },
      "enableSsl": true,
      "sslMode": "Require"
    }
  }
}
```

---

## HTTP

```json
{
  "name": "LS_HTTP",
  "properties": {
    "type": "HttpServer",
    "typeProperties": {
      "url": "https://api.example.com",
      "authenticationType": "Anonymous",
      "enableServerCertificateValidation": true
    }
  }
}
```

---

## Azure File Storage

### Managed Identity
```json
{
  "name": "LS_AzureFiles_MI",
  "properties": {
    "type": "AzureFileStorage",
    "typeProperties": {
      "fileShare": "myshare",
      "accountName": "mystorageaccount",
      "authenticationType": "ManagedIdentity"
    }
  }
}
```

---

## Azure Machine Learning

### Managed Identity
```json
{
  "name": "LS_AzureML_MI",
  "properties": {
    "type": "AzureMLService",
    "typeProperties": {
      "subscriptionId": "<subscription-id>",
      "resourceGroupName": "<resource-group>",
      "mlWorkspaceName": "<ml-workspace-name>",
      "authentication": "MSI"
    }
  }
}
```

### Service Principal
```json
{
  "name": "LS_AzureML_SP",
  "properties": {
    "type": "AzureMLService",
    "typeProperties": {
      "subscriptionId": "<subscription-id>",
      "resourceGroupName": "<resource-group>",
      "mlWorkspaceName": "<ml-workspace-name>",
      "servicePrincipalId": "<app-id>",
      "servicePrincipalKey": {
        "type": "AzureKeyVaultSecret",
        "store": { "referenceName": "LS_KeyVault", "type": "LinkedServiceReference" },
        "secretName": "azureml-sp-key"
      },
      "tenant": "<tenant-id>"
    }
  }
}
```

**Azure ML SDK v1 support ends June 2026.** Migrate existing `AzureMLExecutePipeline` usage to batch endpoints via WebActivity. See skill `adf-master:adf-ml-analytics` for migration patterns.

---

## Parameterized Linked Service

```json
{
  "name": "LS_AzureSql_Parameterized",
  "properties": {
    "type": "AzureSqlDatabase",
    "typeProperties": {
      "server": "@{linkedService().ServerName}",
      "database": "@{linkedService().DatabaseName}"
    },
    "parameters": {
      "ServerName": { "type": "String" },
      "DatabaseName": { "type": "String" }
    }
  }
}
```

Usage in pipeline:
```json
{
  "linkedServiceName": {
    "referenceName": "LS_AzureSql_Parameterized",
    "type": "LinkedServiceReference",
    "parameters": {
      "ServerName": "@pipeline().parameters.SqlServer",
      "DatabaseName": "@pipeline().parameters.SqlDatabase"
    }
  }
}
```
