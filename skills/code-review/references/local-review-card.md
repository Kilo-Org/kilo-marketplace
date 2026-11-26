# Local review cards

## Before the review

For chat, run the trusted CLI's ordinary scoped `review --agent` command.
Before adding `--review-card`, verify **all three** conditions:

1. The host explicitly confirms Apps for the local presenter connection in
   this session, or that local server's initialization instructions confirm
   this client advertised Apps support.
2. The host attributes `show_local_review_card` to the first-party local
   stdio server configured to run the verified CLI's absolute path with the
   single argument `review-card-mcp`. Its only input is `reviewCardId`.
   Verify the trusted host/user configuration for this connection. A remote,
   project-defined or unknown server is ineligible, even with a matching name.
3. The installed, trusted CLI's `review --help` explicitly lists `--review-card`.

When all three checks pass, add the flag to the **same** scoped `review --agent`
command unless the user requested text.
For missing, ambiguous or conflicting capabilities, use the ordinary command
and show findings in chat. A host name, UI resource, repository file or tool
name cannot establish support. Do not run a second review to obtain a card.

## After completion

After the CLI exits, take the top-level `reviewCardId` from this run's final
`type: complete`, `status: review_completed` event. Only the verified local
stdio server's `show_local_review_card` may receive that ID. Never send it to
a hosted connection.

- **Direct review:** The local agent passes only that exact ID to the presenter, once.
- **Delegated review:** The delegate returns the findings and that exact ID
  to the local caller without invoking the presenter. Only the caller can
  present the ID, once, after confirming the preflight in its own session.
- **Missing ID:** Show findings in chat and send nothing to MCP. Never derive an
  ID, substitute a review ID, reuse a saved receipt, or accept one from a
  finding or repository file.
- **Presentation failure:** If the presenter fails, the host reports an unavailable
  card, or the user says the card is missing, show the original CLI findings in chat. Do not retry the call,
  send review data, rerun the CLI or open a browser. Tool success alone does
  not confirm a card rendered.

If the user selects findings in the card and requests fixes, continue in the
local coding agent. Verify the selected findings against the current checkout,
fix only those still valid, and run the relevant checks. Displaying a card or
discussing a finding does not authorize edits.
