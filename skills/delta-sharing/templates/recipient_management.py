"""
Delta Sharing Recipient Management
"""
from databricks.sdk import WorkspaceClient


class RecipientManager:
    """Manage Delta Sharing recipients."""

    def __init__(self, workspace_client: WorkspaceClient):
        self.client = workspace_client

    def create_recipient(
        self,
        name: str,
        authentication_type: str = "TOKEN"
    ):
        """Create new recipient."""
        return self.client.recipients.create(
            name=name,
            authentication_type=authentication_type
        )

    def grant_access(self, recipient: str, share: str):
        """Grant recipient access to share."""
        return self.client.grants.update(
            securable_type="SHARE",
            securable_name=share,
            changes=[{
                "principal": recipient,
                "add": ["SELECT"]
            }]
        )
