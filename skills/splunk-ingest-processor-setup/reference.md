# Splunk Ingest Processor Setup Reference

## Product Surface

This skill covers the Splunk Cloud Platform Ingest Processor solution:

- provisioning and first-time readiness
- user, role, service account, index, lookup, and connection refresh readiness
- source types, event breaking/merging, sample data, and preview workflow
- partitions by host, source, sourcetype, and index where supported
- destination setup for paired Splunk Cloud indexes, Observability Cloud,
  metrics indexes, and Amazon S3
- SPL2 pipelines with route, branch, thru, redact, hash, sample, lookup,
  extract, timestamp, JSON/XML, metrics, OCSF, decrypt, stats, and S3 patterns
- custom pipeline templates under `default/data/spl2`
- Automated Field Extraction UI handoff
- AI-powered data management readiness for onboarding, schema, and pipeline
  recommendations as UI handoff
- Automated Field Extraction exact region allowlist: `us-east-1`,
  `eu-west-1`, `eu-west-2`, `ap-southeast-1`, `ap-southeast-2`,
  `eu-central-1`, `us-west-2`, and `eu-west-3`
- SPL-to-SPL2 conversion review
- apply, edit, remove, refresh, delete, rollback, and support handoffs
- queue, DLQ, Usage Summary, `_internal`, `_audit`, `_metrics`, and destination
  index validation

## Non-Goals

- No private Data Management or Ingest Processor API CRUD is claimed.
- No AI-powered data management API CRUD is claimed.
- No raw secret values are rendered.
- No Splunk Enterprise destination is rendered for IP. Use Edge Processor for
  Splunk Enterprise destinations.
- No real private keys are generated or stored.
- No known issue is hidden: no delivery guarantee, tenant-admin-only pipeline
  access, single-browser-session editing, forwarder `useACK=false`, HEC
  acknowledgement off, and CIDR lookup unsupported are rendered explicitly.

## Destination Policy

Supported Ingest Processor destination families in this skill:

- `splunk_cloud` - paired Splunk Cloud index destinations.
- `observability` - Splunk Observability Cloud deployment destination.
- `metrics_index` - Splunk platform metrics index destination.
- `s3` - Amazon S3 JSON or Parquet archive destination.

Unsupported destination families render a finding and a handoff. The most
important unsupported family is `splunk_enterprise`, which belongs to
`splunk-edge-processor-setup`.

## Limits And Risk Notes

- Pipeline count, lookup size, persistent queue retention, and ingest volume
  limits vary by Splunk Cloud entitlement and service details.
- Branch and route patterns can duplicate data and fill persistent queues when
  one destination is blocked.
- Hashing is not complete anonymization.
- Decrypt is resource-intensive and requires RSA/PKCS#1 v1.5 private-key
  lookup handling.
- `stats` aggregations are batch scoped. Use `sum()/count()` rather than
  `avg()`.
- `logs_to_metrics` requires the documented import command and metric type
  review.
- S3 archives should include downstream Federated Search for Amazon S3 review
  where operators need search access to archived IP output.

## Source Anchors

- About Ingest Processor:
  <https://help.splunk.com/en/data-management/process-data-at-ingest-time/use-ingest-processor/introduction/about-ingest-processor>
- First-time setup:
  <https://help.splunk.com/en/data-management/process-data-at-ingest-time/use-ingest-processor/getting-started/first-time-setup-instructions-for-the-ingest-processor-solution>
- Pipeline syntax:
  <https://help.splunk.com/en/data-management/transform-and-route-data/process-data-at-ingest-time/working-with-pipelines/ingest-processor-pipeline-syntax>
- Create pipelines:
  <https://help.splunk.com/en/data-management/process-data-at-ingest-time/use-ingest-processor/working-with-pipelines/create-pipelines-for-ingest-processor>
- Custom pipeline templates:
  <https://help.splunk.com/en/data-management/transform-and-route-data/process-data-at-ingest-time/working-with-pipelines/create-custom-pipeline-templates>
- Destinations:
  <https://help.splunk.com/en/data-management/process-data-at-ingest-time/use-ingest-processor/send-data-out-from-ingest-processor/how-the-destination-for-ingest-processor-works>
- Queueing:
  <https://help.splunk.com/en/splunk-cloud-platform/process-data-at-ingest-time/use-ingest-processors/monitor-system-health-and-activity/resiliency-and-queueing-in-ingest-processor>
- Release notes:
  <https://help.splunk.com/en/data-management/process-data-at-ingest-time/use-ingest-processor/introduction/release-notes-for-ingest-processor>
