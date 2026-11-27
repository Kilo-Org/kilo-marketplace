# Worked example: ambiguous attachment

Synthetic fixture at 11:00 UTC.

## Available evidence

- A1: Alert AL-12 is firing; its title says "CPU high," but the payload measures
  checkout request failures. It has no incident attached.
- M1: Checkout errors have remained above their baseline for eight minutes.
- L1: Checkout request logs show a matching increase in 502 errors.
- I1: An existing incident concerns search indexing failures in a different region.
- O1: The routing label points to a retired team; fresh ownership is not available.
- D1: No verified shared dependency between the two symptoms has been supplied.

## Example brief

Confirmed: checkout request failures are elevated (M1, L1). The alert title does
not match its metric (A1). The supplied record has no attached incident (A1).
Ownership is uncertain because routing is stale (O1).

Recommend opening a separate incident and proposing a cross-link to I1 while
checking for shared dependency evidence. Similar timing does not establish that
checkout errors belong to the search incident. Ask the commander to identify
the current checkout owner; do not page the retired team.

Revisit attachment if matching errors on a verified shared dependency explain
both failures. No incident was opened or linked, and the alert was not dismissed.

## Counterexample

If fresh routing, matching symptoms, and dependency evidence show this is the
same ongoing outage, recommend attachment instead of opening a duplicate.
