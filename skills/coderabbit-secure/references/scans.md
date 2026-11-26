# Estimate, run and follow a Deep Scan

**Status or cost.** Use `list_security_scans` for history and
`get_security_scan` with the repository, scan ID and code target for progress.
Include scan mode, coverage, findings and actual billed amount when returned.
Unknown cost is distinct from zero. For a cost question, use
`get_security_scan_quote` and report its status, estimate, freshness and
available Deep Scan credits. Convert cents to currency. The quote is for a
full scan. An estimate alone cannot establish the price of a delta or promise
a final bill.

**Start.** Confirm the intended repository and full or delta mode from the
request. Delta requires an eligible completed full scan. Never silently
upgrade to a full scan. For a paid start, show the returned quote and credit
balance and obtain the required spending authorization. If asked what they
may pay beyond credits, subtract the available credits from the estimate
(floor at zero) and label the result an estimate. An unknown credit balance
leaves the out-of-pocket amount unknown. Preserve the user's
cap in the actual request and leave overage disabled unless explicitly
authorized. If the requested spending condition cannot be represented or
verified, explain why before dispatch. Use `start_security_scans` only for
the requested repositories with the code target. Report each repository's
outcome and follow accepted runs using the returned `codeScanId`.

**Recovery.** After a timeout or an uncertain start, inspect scan history
before any retry. For an eligible failed or partial run, follow
`recover_security_scan`'s current retry/resume contract and the user's
spending constraints. Track the new scan ID on success.

**Schedules.** Read `get_security_scan_schedule` first. Summarize the existing
cadence, timezone and paid-use setting. For a requested change, show the next
cadence in human terms and resolve any ambiguous timezone. Use
`save_security_scan_schedule` with the observed revision for an edit or
`previous: null` for creation. A scheduled delta can fall back to a full scan
when its baseline or coverage is insufficient. The delta spend limit does
not cap that full run. If the user requires a maximum for every scheduled
run, resolve that constraint before saving. Recurring paid use requires the
user's explicit approval and appropriate billing access. Delete only the
selected schedule with `delete_security_scan_schedule`, passing its ID and
`expected_revision` from the read. Re-read on conflicts and
report dashboard-managed schedules as such.
