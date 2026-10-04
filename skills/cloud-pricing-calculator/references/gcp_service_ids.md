# GCP Service IDs

Service IDs required for the Cloud Billing API.

## Compute Services

| Service Name | Service ID | Description |
|--------------|------------|-------------|
| Compute Engine | `6F81-5844-456A` | VMs, disks, networking |
| Cloud Storage | `95FF-2EF5-5EA1` | Object storage |
| Cloud SQL | `9662-5216-0528` | Managed databases |
| Cloud Run | `CAE0-46A3-92A8` | Containerized applications |
| GKE | `CC4C-C4B3-0BFC` | Kubernetes Engine |
| Cloud Functions | `C972-494D-87B6` | Serverless functions |
| Cloud BigQuery | `D79A-C5A5-9FD1` | Data warehouse |
| Cloud Spanner | `D17B-C35B-5853` | Distributed database |
| Cloud Pub/Sub | `D74F-8A19-3A80` | Message service |
| Cloud Load Balancing | `8F81-A7A1-4C17` | Load balancing |

## Storage Services

| Service Name | Service ID | Description |
|--------------|------------|-------------|
| Cloud Storage | `95FF-2EF5-5EA1` | Multi-regional object storage |
| Persistent Disk | `6F81-5844-456A` | Part of Compute Engine |
| Filestore | `E505-85F8-4B1B` | Managed NFS |

## Database Services

| Service Name | Service ID | Description |
|--------------|------------|-------------|
| Cloud SQL | `9662-5216-0528` | MySQL, PostgreSQL, SQL Server |
| Cloud Spanner | `D17B-C35B-5853` | Globally distributed SQL |
| Firestore | `F3A9-2B7C-1D8E` | NoSQL document database |
| Cloud Bigtable | `B761-A47C-2E39` | Wide-column NoSQL |
| Memorystore | `M294-7B1C-9D52` | Managed Redis/Memcached |



## API Discovery

To find additional service IDs:

```bash
curl -s "https://cloudbilling.googleapis.com/v1/services?key=YOUR_API_KEY" | \
  jq '.services[] | {name: .displayName, id: .serviceId}'
```

## Usage in API Calls

```bash
# Get all SKUs for a service
curl -s "https://cloudbilling.googleapis.com/v1/services/{SERVICE_ID}/skus?key=YOUR_KEY"

# Example: Compute Engine SKUs
curl -s "https://cloudbilling.googleapis.com/v1/services/6F81-5844-456A/skus?key=YOUR_KEY"
```
