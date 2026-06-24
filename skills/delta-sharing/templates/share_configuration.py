"""
Delta Sharing Configuration Template
"""
from databricks.sdk import WorkspaceClient
from typing import List, Dict, Any


class DeltaShareManager:
    """Manage Delta Sharing configuration."""

    def __init__(self, workspace_client: WorkspaceClient):
        self.client = workspace_client

    def create_share(self, share_name: str, comment: str = None) -> Dict:
        """Create new Delta share."""
        return self.client.shares.create(
            name=share_name,
            comment=comment
        )

    def add_tables_to_share(
        self,
        share_name: str,
        tables: List[Dict[str, str]]
    ):
        """Add tables to share."""
        for table in tables:
            self.client.shares.update(
                name=share_name,
                updates=[{
                    "action": "ADD",
                    "data_object": {
                        "name": table["full_name"],
                        "data_object_type": "TABLE"
                    }
                }]
            )
