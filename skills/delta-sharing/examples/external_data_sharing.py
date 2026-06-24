"""
External Data Sharing Example
Set up Delta Sharing for external partners.
"""
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

    print(f"Share created: {share.name}")
    print(f"Recipient token: {recipient.activation_url}")
