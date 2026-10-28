"""
External Data Sharing Example
Set up Delta Sharing for external partners.
"""
from pathlib import Path

from databricks.sdk import WorkspaceClient


def setup_external_sharing():
    """Configure sharing with external partner."""
    w = WorkspaceClient()

    # Create share
    share = w.shares.create(
        name="partner_analytics_share",
        comment="Analytics data for external partner"
    )

    # Add tables
    w.shares.update(
        name="partner_analytics_share",
        updates=[{
            "action": "ADD",
            "data_object": {
                "name": "catalog.schema.aggregated_metrics",
                "data_object_type": "TABLE"
            }
        }]
    )

    # Create recipient
    recipient = w.recipients.create(
        name="partner_company",
        authentication_type="TOKEN"
    )

    # Grant access
    w.grants.update(
        securable_type="SHARE",
        securable_name="partner_analytics_share",
        changes=[{
            "principal": "partner_company",
            "add": ["SELECT"]
        }]
    )

    activation_file = Path.home() / ".delta-sharing" / "partner_company.activation-url"
    activation_file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    activation_file.write_text(recipient.activation_url, encoding="utf-8")
    activation_file.chmod(0o600)

    print(f"Share created: {share.name}")
    print(f"Activation URL stored at: {activation_file}")
