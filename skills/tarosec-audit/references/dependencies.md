# Dependency and supply-chain triage

- Read existing reports first. Record tool, version, date, command, exit status,
  ecosystem and scanned lockfile/revision. A parse error is a coverage gap.
- Compare each advisory with the **resolved** version and dependency path, not the
  declared range. A stale report does not prove the current package is affected.
- Separate: affected installation → reachable vulnerable code → exploitable in
  deployment. Dev-only and test-only paths are noted, not dismissed.
- Verify IDs and affected ranges against an authoritative advisory (vendor, OSV,
  GHSA, NVD) when network use is approved; otherwise mark them unverified. KEV and
  EPSS status are current facts: cite a dated source or say unknown.
- CI/CD: unpinned actions, `pull_request_target` with checkout of PR code, secrets
  exposed to forks, writable tokens, unverified artifact downloads, install scripts.
- Never auto-fix, install packages or upload manifests under read-only authorization.
