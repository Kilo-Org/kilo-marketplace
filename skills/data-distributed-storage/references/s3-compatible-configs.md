# S3-Compatible Configurations

## AWS SDK Usage (Boto3)

```python
import boto3

s3 = boto3.client(
    "s3",
    endpoint_url="https://minio.datalake.internal:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin",
    verify="/path/to/private-ca-bundle.pem",
    config=boto3.session.Config(
        signature_version="s3v4",
        s3={"addressing_style": "path"},
        retries={"max_attempts": 3, "mode": "adaptive"}
    )
)

s3.create_bucket(Bucket="analytics-data")
s3.put_bucket_versioning(
    Bucket="analytics-data",
    VersioningConfiguration={"Status": "Enabled"}
)

s3.upload_file(
    Filename="/data/export.parquet",
    Bucket="analytics-data",
    Key="exports/2026/05/22/sales.parquet"
)

url = s3.generate_presigned_url(
    ClientMethod="get_object",
    Params={"Bucket": "analytics-data", "Key": "exports/2026/05/22/sales.parquet"},
    ExpiresIn=604800
)
```

## Bucket Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "AWS": ["arn:aws:iam::123456789012:role/analytics-role"] },
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::analytics-data/*",
        "arn:aws:s3:::analytics-data"
      ],
      "Condition": {
        "IpAddress": { "aws:SourceIp": "10.0.0.0/8" }
      }
    }
  ]
}
```

## Lifecycle Rules

```yaml
rules:
  - id: expire_temp
    status: Enabled
    filter:
      prefix: temp/
    expiration:
      days: 7
  - id: tier_to_cold
    status: Enabled
    filter:
      prefix: logs/
    transitions:
      - days: 30
        storage_class: GLACIER_IR
      - days: 90
        storage_class: DEEP_ARCHIVE
  - id: delete_old_exports
    status: Enabled
    filter:
      prefix: exports/
    expiration:
      days: 365
    noncurrent_version_expiration:
      noncurrent_days: 30
```

## Multipart Upload Config

```python
from boto3.s3.transfer import TransferConfig

config = TransferConfig(
    multipart_threshold=64 * 1024 * 1024,
    multipart_chunksize=64 * 1024 * 1024,
    max_concurrency=10,
    use_threads=True
)

s3.upload_file(
    "large_file.parquet", "analytics-data", "imports/large_file.parquet",
    Config=config
)
```

## Bucket Notification (MinIO)

```yaml
events:
  - s3:ObjectCreated:*
  - s3:ObjectRemoved:*
queue:
  arn: minio:sqs::kafka:kafka-cluster
  topic: minio-events
```
