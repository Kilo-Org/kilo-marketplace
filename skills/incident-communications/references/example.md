# Worked example: no defensible recovery estimate

Synthetic fixture at 12:05 UTC; the user requests a customer-update draft.

## Available evidence

- M1: Checkout failures are elevated in region A, 11:55–12:05.
- L1: Checkout request logs corroborate failed payment attempts in that region.
- I1: The incident commander says the cause remains unknown, checks of recent
  changes are underway, and no defensible recovery estimate exists yet.
- I2: The commander approved the next customer update for 12:20 UTC.
- V1: A vendor reports degradation in region B. No match to region A is verified.
- P1: Approved company template asks for impact, actions, estimate, and next update.

## Customer draft

Checkout is failing for customers in region A. We are checking recent changes
and affected dependencies. We have not yet identified the cause, and recovery
time is not yet known. Our next update will be at 12:20 UTC.

## Internal verification notes

Impact is corroborated by M1 and L1. Actions and uncertainty come from I1; the
update commitment comes from I2. Ask the commander for a supported recovery
range when one becomes available. Do not invent one to fill P1. Keep V1 internal
and unconfirmed; its affected region differs. This draft has not been published.

## Counterexample

If the commander provides a supported estimate of 20–40 minutes conditional on
rollback restoring the error rate, label it an estimate and retain the condition.
Do not turn that range into a guaranteed deadline or narrow it without evidence.
