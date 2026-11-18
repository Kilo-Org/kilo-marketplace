# Routing

| Mode or intent | Skill and use |
| --- | --- |
| Project path, scan, audit, source or configuration review | Audit, read-only |
| Red, attack surface review | Red, supplied records only |
| Blue, logs, hunting, or incident | Blue for offline triage |
| Purple or detection validation | Purple for recorded observations |
| Simulate, generate events, or replay | Simulate for offline fixtures |
| Verify | Audit for a source fix, Purple for detection retest |
| Intel | Audit for supplied advisory review |
| Report | Summarize supplied records with their evidence IDs and limits |
| Help | Explain the modes and available skills |

The routing helper accepts a normalized mode. To route natural language, inspect
the requested action and artifact first. For ambiguous verification, use Audit
unless the evidence describes a defensive exercise. Use `--evidence exercise`
for that case. Report when source artifacts are missing. Current intelligence
requires an authorized source lookup and is outside the offline fallback.

Pass the names of specialists that the host exposes to this session as repeated
`--available` flags. Run `python3 scripts/route.py help` for the contract.
An installed specialist owns the work. For a missing specialist, use the
`installSelector` in the response with the project's Skills CLI source.
An entry-only install can provide a read-only inventory of supplied artifacts,
cite existing records, and help the user choose a workflow.
