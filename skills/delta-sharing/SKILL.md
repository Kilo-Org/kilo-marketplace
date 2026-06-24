---
name: "delta-sharing"
description: "Delta Sharing configuration, monitoring, and recipient management for secure cross-organization data sharing."
metadata:
  category: data
  source:
    repository: "https://github.com/vivekgana/databricks-platform-marketplace"
    path: "plugins/databricks-engineering/skills/delta-sharing"
    license_path: "LICENSE"
---

# Delta Sharing Skill

## Overview

Delta Sharing is an open protocol for secure data sharing across organizations. This skill covers share configuration, recipient management, access control, and usage monitoring.

**Key Benefits:**
- Secure cross-organization sharing
- No data duplication
- Real-time data access
- Centralized access control
- Usage tracking and auditing
- Open standard (works with any platform)

## When to Use This Skill

Use Delta Sharing when you need to:
- Share data with external partners
- Enable cross-workspace data access
- Distribute data products to consumers
- Implement multi-tenant data access
- Track data consumption patterns
- Maintain centralized governance

## Core Concepts

### 1. Share Configuration

**Create and Configure Shares:**
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Create share
share = w.shares.create(
    name="partner_analytics_share",
    comment="Analytics data for external partners"
)

# Add tables to share
w.shares.update(
    name="partner_analytics_share",
    updates=[
        {
            "action": "ADD",
            "data_object": {
                "name": "catalog.schema.customer_metrics",
                "data_object_type": "TABLE",
                "comment": "Aggregated customer metrics"
            }
        },
        {
            "action": "ADD",
            "data_object": {
                "name": "catalog.schema.product_sales",
                "data_object_type": "TABLE"
            }
        }
    ]
)
```

### 2. Recipient Management

**Create and Manage Recipients:**
```python
# Create recipient
recipient = w.recipients.create(
    name="acme_corp",
    comment="ACME Corporation partner",
    authentication_type="TOKEN"
)

# Get activation URL for recipient
activation_url = recipient.activation_url
print(f"Share this URL with recipient: {activation_url}")

# Grant access to share
w.grants.update(
    securable_type="SHARE",
    securable_name="partner_analytics_share",
    changes=[{
        "principal": "acme_corp",
        "add": ["SELECT"]
    }]
)
```

### 3. Access Control

**Manage Permissions:**
```python
# List current permissions
permissions = w.grants.get_effective(
    securable_type="SHARE",
    full_name="partner_analytics_share"
)

# Revoke access
w.grants.update(
    securable_type="SHARE",
    securable_name="partner_analytics_share",
    changes=[{
        "principal": "acme_corp",
        "remove": ["SELECT"]
    }]
)

# Grant access to specific tables only
w.grants.update(
    securable_type="TABLE",
    full_name="catalog.schema.customer_metrics",
    securable_type="SHARE",
    securable_name="partner_analytics_share",
    changes=[{
        "principal": "acme_corp",
        "add": ["SELECT"]
    }]
)
```

### 4. Usage Monitoring

**Track Share Usage:**
```python
def monitor_share_usage(spark, share_name: str, days: int = 7):
    """Monitor Delta Sharing usage."""
    query = f"""
    SELECT
        date_trunc('day', request_time) as date,
        recipient_name,
        table_name,
        COUNT(*) as request_count,
        SUM(rows_returned) as total_rows,
        SUM(bytes_transferred) as total_bytes
    FROM system.access.audit
    WHERE share_name = '{share_name}'
      AND request_time >= current_date() - INTERVAL {days} DAYS
    GROUP BY 1, 2, 3
    ORDER BY 1 DESC, 4 DESC
    """

    return spark.sql(query)


# Get usage metrics
usage_df = monitor_share_usage(spark, "partner_analytics_share")
usage_df.show()
```

## Implementation Patterns

### Pattern 1: Multi-Tenant Sharing

**Separate Shares per Tenant:**
```python
class MultiTenantSharingManager:
    """Manage multi-tenant data sharing."""

    def __init__(self, workspace_client: WorkspaceClient):
        self.client = workspace_client

    def setup_tenant_share(
        self,
        tenant_name: str,
        tables: List[str],
        tenant_email: str
    ):
        """Set up complete sharing for a tenant."""
        share_name = f"{tenant_name}_share"

        # Create share
        self.client.shares.create(
            name=share_name,
            comment=f"Data share for {tenant_name}"
        )

        # Add tables
        for table in tables:
            self.client.shares.update(
                name=share_name,
                updates=[{
                    "action": "ADD",
                    "data_object": {
                        "name": table,
                        "data_object_type": "TABLE"
                    }
                }]
            )

        # Create recipient
        recipient = self.client.recipients.create(
            name=tenant_name,
            comment=f"Recipient for {tenant_name}",
            authentication_type="TOKEN"
        )

        # Grant access
        self.client.grants.update(
            securable_type="SHARE",
            securable_name=share_name,
            changes=[{
                "principal": tenant_name,
                "add": ["SELECT"]
            }]
        )

        return {
            "share_name": share_name,
            "recipient": tenant_name,
            "activation_url": recipient.activation_url,
            "tables": tables
        }
```

### Pattern 2: Row-Level Security

**Implement RLS for Shared Data:**
```python
import dlt
from pyspark.sql.functions import *


@dlt.table(
    name="customer_data_with_rls",
    comment="Customer data with row-level security"
)
def customer_data_with_tenant_filter():
    """
    Apply row-level security for multi-tenant sharing.

    Each recipient sees only their tenant's data.
    """
    return (
        dlt.read("silver_customer_data")
        .withColumn("tenant_id", col("customer_id").substr(1, 3))
        .select(
            "customer_id",
            "tenant_id",
            "customer_name",
            "email",
            "created_date"
        )
    )


# Share with partition filtering
def create_tenant_specific_share(
    tenant_id: str,
    source_table: str,
    share_name: str
):
    """
    Create share with automatic tenant filtering.

    Uses partition pruning for efficient filtering.
    """
    w = WorkspaceClient()

    # Create view with tenant filter
    view_name = f"{source_table}_{tenant_id}_view"

    spark.sql(f"""
    CREATE OR REPLACE VIEW {view_name} AS
    SELECT * FROM {source_table}
    WHERE tenant_id = '{tenant_id}'
    """)

    # Share the view
    w.shares.create(name=share_name)
    w.shares.update(
        name=share_name,
        updates=[{
            "action": "ADD",
            "data_object": {
                "name": view_name,
                "data_object_type": "VIEW"
            }
        }]
    )
```

### Pattern 3: Usage Analytics

**Comprehensive Usage Tracking:**
```python
class SharingAnalytics:
    """Analyze Delta Sharing usage patterns."""

    def __init__(self, spark):
        self.spark = spark

    def get_most_accessed_tables(self, days: int = 30):
        """Find most accessed shared tables."""
        return self.spark.sql(f"""
        SELECT
            table_name,
            COUNT(DISTINCT recipient_name) as unique_recipients,
            COUNT(*) as total_requests,
            SUM(rows_returned) as total_rows,
            AVG(query_duration_ms) as avg_duration_ms
        FROM system.access.audit
        WHERE event_type = 'deltaSharing'
          AND request_time >= current_date() - INTERVAL {days} DAYS
        GROUP BY table_name
        ORDER BY total_requests DESC
        LIMIT 20
        """)

    def get_recipient_activity(self, recipient_name: str, days: int = 7):
        """Detailed activity for specific recipient."""
        return self.spark.sql(f"""
        SELECT
            date_trunc('hour', request_time) as hour,
            table_name,
            COUNT(*) as requests,
            SUM(rows_returned) as rows,
            SUM(bytes_transferred) / 1024 / 1024 as mb_transferred
        FROM system.access.audit
        WHERE recipient_name = '{recipient_name}'
          AND request_time >= current_date() - INTERVAL {days} DAYS
        GROUP BY 1, 2
        ORDER BY 1 DESC
        """)

    def detect_anomalies(self, share_name: str):
        """Detect unusual access patterns."""
        return self.spark.sql(f"""
        WITH daily_stats AS (
            SELECT
                date_trunc('day', request_time) as date,
                recipient_name,
                COUNT(*) as daily_requests
            FROM system.access.audit
            WHERE share_name = '{share_name}'
              AND request_time >= current_date() - INTERVAL 30 DAYS
            GROUP BY 1, 2
        ),
        stats AS (
            SELECT
                recipient_name,
                AVG(daily_requests) as avg_requests,
                STDDEV(daily_requests) as stddev_requests
            FROM daily_stats
            GROUP BY recipient_name
        )
        SELECT
            d.date,
            d.recipient_name,
            d.daily_requests,
            s.avg_requests,
            s.stddev_requests,
            CASE
                WHEN d.daily_requests > s.avg_requests + 2 * s.stddev_requests
                THEN 'ANOMALY_HIGH'
                WHEN d.daily_requests < s.avg_requests - 2 * s.stddev_requests
                THEN 'ANOMALY_LOW'
                ELSE 'NORMAL'
            END as status
        FROM daily_stats d
        JOIN stats s ON d.recipient_name = s.recipient_name
        WHERE date >= current_date() - INTERVAL 7 DAYS
        ORDER BY d.date DESC, d.daily_requests DESC
        """)
```

### Pattern 4: Automated Share Management

**CI/CD for Share Configuration:**
```python
"""
Automated share management from configuration.
"""
import yaml
from typing import Dict, List, Any


class ShareConfigManager:
    """Manage shares from YAML configuration."""

    def __init__(self, workspace_client: WorkspaceClient):
        self.client = workspace_client

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load share configuration from YAML."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def apply_config(self, config: Dict[str, Any]):
        """Apply share configuration."""
        for share_config in config.get('shares', []):
            self._create_or_update_share(share_config)

        for recipient_config in config.get('recipients', []):
            self._create_or_update_recipient(recipient_config)

        for grant_config in config.get('grants', []):
            self._apply_grants(grant_config)

    def _create_or_update_share(self, config: Dict[str, Any]):
        """Create or update a share."""
        try:
            existing = self.client.shares.get(name=config['name'])
            print(f"Share {config['name']} already exists")
        except:
            self.client.shares.create(
                name=config['name'],
                comment=config.get('comment', '')
            )
            print(f"Created share: {config['name']}")

        # Add tables
        for table in config.get('tables', []):
            self.client.shares.update(
                name=config['name'],
                updates=[{
                    "action": "ADD",
                    "data_object": {
                        "name": table,
                        "data_object_type": "TABLE"
                    }
                }]
            )
```

**Example Configuration (shares.yaml):**
```yaml
shares:
  - name: partner_analytics_share
    comment: Analytics data for partners
    tables:
      - catalog.analytics.customer_metrics
      - catalog.analytics.product_performance
      - catalog.analytics.sales_summary

recipients:
  - name: acme_corp
    comment: ACME Corporation
    authentication_type: TOKEN
    email: data-team@acme.com

  - name: globex_inc
    comment: Globex Inc
    authentication_type: TOKEN
    email: analytics@globex.com

grants:
  - share: partner_analytics_share
    recipient: acme_corp
    permissions: [SELECT]

  - share: partner_analytics_share
    recipient: globex_inc
    permissions: [SELECT]
```

## Best Practices

### 1. Security

- Use token-based authentication
- Implement row-level security when needed
- Regular audit of access permissions
- Monitor for unusual access patterns
- Rotate recipient tokens periodically

### 2. Performance

- Share aggregated data when possible
- Use partition pruning for large tables
- Monitor query performance
- Implement caching strategies
- Limit result set sizes

### 3. Governance

- Document all shares and recipients
- Maintain share configuration in version control
- Regular access reviews
- Clear data ownership
- Defined SLAs for shared data

### 4. Monitoring

```python
# Set up alerts for anomalous usage
def check_usage_threshold(spark, share_name: str, threshold_gb: float = 100):
    """Alert if daily data transfer exceeds threshold."""
    query = f"""
    SELECT
        SUM(bytes_transferred) / 1024 / 1024 / 1024 as gb_transferred
    FROM system.access.audit
    WHERE share_name = '{share_name}'
      AND date_trunc('day', request_time) = current_date()
    """

    result = spark.sql(query).first()
    gb_transferred = result['gb_transferred'] or 0

    if gb_transferred > threshold_gb:
        send_alert(
            f"Share {share_name} transferred {gb_transferred:.2f}GB today, "
            f"exceeding threshold of {threshold_gb}GB"
        )
```

## Common Pitfalls to Avoid

Don't:
- Share raw PII without review
- Neglect access auditing
- Skip documentation
- Ignore usage monitoring
- Hard-code credentials

Do:
- Implement data masking for sensitive fields
- Regular access audits
- Document all shares
- Monitor usage patterns
- Use secure credential management

## Complete Examples

See `/examples/` directory for:
- `external_data_sharing.py`: Complete external sharing setup
- `multi_tenant_sharing.py`: Multi-tenant implementation

## Related Skills

- `data-products`: Share data products
- `data-quality`: Ensure shared data quality
- `medallion-architecture`: Share gold layer tables
- `cicd-workflows`: Automate share management

## References

- [Delta Sharing Protocol](https://github.com/delta-io/delta-sharing)
- [Databricks Delta Sharing Docs](https://docs.databricks.com/data-sharing/index.html)
- [Delta Sharing Security](https://docs.databricks.com/security/delta-sharing.html)
