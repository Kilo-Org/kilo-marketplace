# SPL2 Pipeline Kit Research Ledger

- 2026-05-17: Ingest Processor docs identify SPL2 runtime profile
  `ingestProcessor` and require `$pipeline`, `from $source`, and `into
  $destination`.
- 2026-05-17: Supported Ingest Processor commands include `branch`, `decrypt`,
  `eval`, `expand`, `fields`, `flatten`, `from`, `into`, `lookup`, `mvexpand`,
  `ocsf`, `rename`, `replace`, `rex`, `route`, `stats`, `thru`, and `where`.
- 2026-05-17: Logs-to-metrics examples import `logs_to_metrics` from
  `/splunk.ingest.commands`; lint must understand `import`, not just pipe
  command names.
- 2026-05-17: Custom pipeline templates are SPL2 app modules under
  `default/data/spl2` and use `@template` metadata.
- 2026-05-17: PCRE2 is the current regex target. Named captures should use the
  `(?P<fieldName>...)` style documented by Splunk.
