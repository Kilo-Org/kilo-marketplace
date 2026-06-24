"""
Delta Sharing Usage Monitoring
"""
from databricks.sdk import WorkspaceClient
from datetime import datetime, timedelta


class SharingMonitor:
    """Monitor Delta Sharing usage."""

    def __init__(self, workspace_client: WorkspaceClient):
        self.client = workspace_client

    def get_share_usage(self, share_name: str, days: int = 7):
        """Get usage metrics for share."""
        # Query system tables for usage data
        query = f"""
        SELECT
            date_trunc('day', request_time) as date,
            recipient_name,
            COUNT(*) as request_count,
            SUM(bytes_transferred) as total_bytes
        FROM system.access.table_lineage
        WHERE share_name = '{share_name}'
          AND request_time >= current_date() - INTERVAL {days} DAYS
        GROUP BY 1, 2
        ORDER BY 1 DESC
        """
        return query
