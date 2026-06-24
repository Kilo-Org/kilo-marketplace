---
name: "gcs-lifecycle-policy"
description: "This skill should be used when designing, reviewing, or changing Google Cloud Storage lifecycle rules for object deletion, storage-class transitions, version cleanup, or retention-aware cost control. It should not activate for general GCS administration."
metadata:
  category: data
  source:
    repository: "https://github.com/jeremylongshore/claude-code-plugins-plus-skills"
    path: "skills/14-gcp-skills/gcs-lifecycle-policy"
    license_path: "LICENSE"
---

# GCS Lifecycle Policy

Design and validate lifecycle rules for a specific Google Cloud Storage bucket.

## Activation and Composition

- Activate only for lifecycle conditions or actions, including age, creation time, live/noncurrent state, version count, deletion, and storage-class transitions.
- Defer bucket creation, IAM, encryption, transfer, and general storage operations to a broader Google Cloud Storage skill.
- Compose with security or compliance guidance when retention policies, object holds, Bucket Lock, or regulated data constrain lifecycle behavior.
- Compose with cost-optimization guidance when choosing transition timing, but keep the resulting lifecycle rules in this skill.

## Workflow

1. Identify the target bucket, current lifecycle configuration, versioning state, retention policy, default storage class, and any object holds.
2. Clarify the desired outcome and the exact object population affected, including prefixes, suffixes, age, custom time, and live/noncurrent state.
3. Evaluate rule interactions and ordering. Multiple matching actions can apply, and deletion or transition rules may affect more objects than intended.
4. Produce the requested JSON, Terraform, or `gcloud storage` configuration using only supported GCS lifecycle fields.
5. Validate the configuration syntax and explain representative objects that will and will not match each rule.
6. Before applying a change, show the current and proposed behavior and obtain confirmation for deletion, archival, or broad-scope rules.
7. Re-read the bucket configuration after applying and report the effective lifecycle rules.

## Safety

- Never treat lifecycle changes as immediate cleanup; GCS evaluates rules asynchronously.
- Never assume lifecycle rules override retention policies or holds.
- Avoid bucket-wide deletion rules unless the user explicitly confirms the scope and retention consequences.
- Preserve unrelated existing rules when adding or changing one rule.
- Prefer dry review of generated configuration when credentials, bucket identity, or current policy cannot be verified.

## Output

Return:

- target bucket and assumptions
- current versus proposed rules
- configuration in the requested format
- examples of matching and nonmatching objects
- retention, versioning, and cost implications
- validation or post-apply verification results

## References

- [Object Lifecycle Management](https://cloud.google.com/storage/docs/lifecycle)
- [Lifecycle configuration](https://cloud.google.com/storage/docs/managing-lifecycles)
- [Object holds and retention](https://cloud.google.com/storage/docs/object-holds)
