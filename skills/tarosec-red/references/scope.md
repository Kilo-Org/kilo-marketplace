# Scope rules

- **Exclusions win** over any target match.
- A host match does not approve another port, scheme or sibling path. A URL-prefix
  target is segment-bound: `/api/` does not include `/api-admin/`.
- Every redirect hop and every DNS answer is a new scope check. Stop on an
  excluded or unlisted address; a pre-flight DNS list cannot prevent rebinding.
- Never widen an IP to its CIDR, a domain to its subdomains, or a program's named
  asset to "related" assets.
- Reject ambiguous inputs: userinfo in URLs, mixed encodings, dot segments,
  numeric/IPv6 forms that differ from the listed value.
- Passive recon means supplied local material only (no DNS, WHOIS, HTTP, CT log or
  search-engine queries) unless those lookups are approved: they reveal interest
  in the target and may hit third-party services.
- Budgets (rate, total requests, duration) are hard ceilings; exhausting one is a
  stop condition, not a reason to slow down and continue.
