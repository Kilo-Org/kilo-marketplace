# Detection engineering

1. **Start from behavior.** Describe the observed or emulated behavior and the
   data source fields that show it. Name the ATT&CK technique (verified ID).
2. **Pick the format the user runs** (Sigma, KQL, SPL, EQL, YARA). Don't translate
   to a backend you cannot test; say the translation is untested.
3. **Ship test cases with the rule:** at least one true-positive sample, one
   near-miss benign sample, and the expected match result for each. Use sanitized
   or synthetic events.
4. **State blind spots:** evasions the rule won't catch, required fields/sources,
   expected volume and false-positive drivers.
5. **Validate offline first.** If a local engine (e.g. `sigma` CLI) is available and
   approved, run the tests; otherwise mark rule tests **Not Run**.
6. **Hand to purple.** A new rule becomes an expected detection in a
   `tarosec-purple` exercise step; coverage is claimed only after a Detected outcome.

Deploying a rule to a production SIEM/EDR is a production change and needs
explicit approval.
