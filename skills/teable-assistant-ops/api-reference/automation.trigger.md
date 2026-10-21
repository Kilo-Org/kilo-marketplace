# Automation Trigger Configuration

Triggers define WHEN an automation should run. Each trigger type has specific configuration requirements.

## Trigger Types

### 1. recordCreated - When Record Created
Triggers when a new record is created in a table.

```json
{
  "type": "recordCreated",
  "config": {
    "tableId": "tblXXXXXXX",           // Required: Table to watch
    "filter": { ... }                  // Optional: Additional filter conditions
  }
}
```

**Output Variables (accessible by subsequent actions):**
- `record.id` - The created record ID
- `record.fields.{fieldName}` - Field values of the created record
- `user` - User who created the record

### 2. recordUpdated - When Record Updated
Triggers when an existing record is modified.

```json
{
  "type": "recordUpdated",
  "config": {
    "tableId": "tblXXXXXXX",           // Required: Table to watch
    "watchFieldIds": ["fldXXX", ...],  // Optional: Only trigger when these fields change
    "filter": { ... }                  // Optional: Additional filter conditions
  }
}
```

**Output Variables:**
- `record.id` - The updated record ID
- `record.fields.{fieldName}` - Current field values
- `record.oldFields.{fieldName}` - Previous field values (before update)
- `user` - User who updated the record

### 3. recordMatchesConditions - When Record Matches Conditions
Triggers when a record transitions from non-matching to matching the specified filter conditions (on both creation and update events).

```json
{
  "type": "recordMatchesConditions",
  "config": {
    "tableId": "tblXXXXXXX",
    "filter": {                         // REQUIRED: Filter conditions to match
      "conjunction": "and",
      "filterSet": [
        { "fieldId": "fldXXX", "operator": "is", "value": "Done" }
      ]
    }
  }
}
```
For detailed filter syntax, see `view.filter` topic

**Output Variables:**
- `record.id` - The record ID
- `record.fields.{fieldName}` - Current field values
- `record.oldFields.{fieldName}` - Previous field values (before update, if applicable)
- `user` - User whose action caused the record to match

### 4. formSubmitted - When Form Submitted
Triggers when a form is submitted.

```json
{
  "type": "formSubmitted",
  "config": {
    "tableId": "tblXXXXXXX",           // Required: Table with the form
    "formId": "viwXXXXXXX"             // Required: The form view ID
  }
}
```

**Output Variables:**
- `record.id` - The created record ID
- `record.fields.{fieldName}` - Submitted field values
- `user` - Submitter (anonymous submissions may have empty fields)

### 5. scheduledTime - At Scheduled Time
Triggers on a schedule.

**Required fields:**
- `starting` — ISO datetime string (when the schedule becomes active)
- `tz` — IANA timezone, e.g., `"Asia/Shanghai"`
- `timing` — object (see below)

**Optional fields:**
- `ending` — ISO datetime string; must be in the future

**`timing.type` enum (exact values):** `"minutes" | "hours" | "days" | "weeks" | "months" | "OneTime"`
⚠️ NOT `"daily"` / `"weekly"` / `"monthly"` — those are wrong.

**Per-variant required sub-fields:**
- `minutes` → `interval: 1..60`
- `hours` → `interval: 1..24`
- `days` → `interval: 1..31`, `triggerTime: { hour: 0..23, minute: 0..59 }`
- `weeks` → `interval: 1..52`, `weekdays: ('MO'|'TU'|'WE'|'TH'|'FR'|'SA'|'SU')[]`, `triggerTime`
- `months` → `interval: 1..12`, `daysOfMonth: (1..31 | -1)[]` (`-1` = last day of month), `triggerTime`
- `OneTime` → no extra fields

⚠️ For `days`/`weeks`/`months`, `triggerTime` is an **object** `{hour, minute}` — NOT a `"HH:mm"` string.

**Canonical example (daily 09:00 Shanghai):**
```json
{
  "type": "scheduledTime",
  "config": {
    "starting": "2026-04-21T09:00:00.000Z",
    "tz": "Asia/Shanghai",
    "timing": {
      "type": "days",
      "interval": 1,
      "triggerTime": { "hour": 9, "minute": 0 }
    }
  }
}
```

**Every-15-minutes example:**
```json
{
  "type": "scheduledTime",
  "config": {
    "starting": "2026-04-21T09:00:00.000Z",
    "tz": "Asia/Shanghai",
    "timing": { "type": "minutes", "interval": 15 }
  }
}
```

**Output Variables (top-level, not under `meta`):**
- `actualTriggeredTime` - ISO 8601 string — when the trigger actually fired
- `expectTriggerTime` - ISO 8601 string — when the trigger was scheduled to fire
- `nextTriggerTime` - ISO 8601 string — next planned firing (`undefined` for the last run of a bounded schedule)

Note: the timezone is part of the trigger config, not the output. Parse the ISO timestamps with a date library if you need local-time formatting.

### 6. buttonClick - When Button Clicked
Triggers when a button field is clicked.

```json
{
  "type": "buttonClick",
  "config": {
    "tableId": "tblXXXXXXX",             // Required: Table containing the button
    "watchFieldIds": ["fldXXXXXXX"]      // Required: Button field IDs to watch (use ["all"] for any button)
  }
}
```

**Output Variables:**
- `record.id` - The record where button was clicked
- `record.fields.{fieldName}` - Field values of that record
- `user` - User who clicked the button

### 7. webhook - When Webhook Received
Triggers when an external HTTP request is sent to the webhook endpoint. All of its settings go under `webhookConfig`:

```json
{
  "triggerType": "webhook",
  "webhookConfig": {
    "authorization": { "type": "none" },
    "response": {
      "mode": "custom",
      "body": "{\"challenge\":\"{{body.challenge}}\"}"
    }
  }
}
```

**Endpoint:** The tool returns `webhook.url` (plus `webhook.token` for bearer auth), and `teable automation get` returns the same. External services POST JSON to that URL, with the bearer in the `Authorization` header:

```
curl -X POST <webhook.url> -H 'Authorization: Bearer <webhook.token>' -H 'Content-Type: application/json' -d '{"hello":"world"}'
```

**Output Variables:**
- `body` - The parsed JSON body of the incoming request

**Security:** Use bearer token authorization for production webhooks. Set `authorization.type` to `"bearer"` and the tool generates the token for you.

**Synchronous Response:** Optional - without it the endpoint returns a fixed acknowledgement. Slack and Feishu / Lark verify a subscription URL by posting a `challenge` that must be echoed back verbatim, or the URL cannot be saved on their side.

`response.body` is a template: `{{body.challenge}}` reads the same path the trigger's output variables use, so anything visible in a test run can be inserted.

Notes:
- `response.statusCode` defaults to 200; `response.contentType` defaults to `application/json` - use `text/plain` to reply with raw text.
- On an update, omitting `response` leaves a stored one untouched; pass `"response": { "mode": "default" }` to go back to the fixed acknowledgement.
- Do not combine a handshake response with bearer authorization - neither platform can send an `Authorization` header.
- The handshake request still runs the workflow. Add a condition on `body.type == "url_verification"` if later steps should skip it.

### 8. emailReceived - When Email Received
Triggers when a new email is received. Supports IMAP connection.

**IMAP Configuration:**
```json
{
  "triggerType": "emailReceived",
  "emailReceivedConfig": {
    "connectionType": "imap",
    "host": "imap.example.com",
    "port": 993,
    "secure": true,
    "user": "user@example.com",
    "password": { "alias": "IMAP_PASSWORD" },
    "mailbox": "INBOX",
    "pollIntervalMinutes": 10
  }
}
```
`password` is a binding to a secret granted to the workflow, never the password itself - a plaintext password in the config is rejected.

Setup flow:
1. `teable automation setup-trigger --trigger-type emailReceived --email-received-config '{...,"password":{"alias":"IMAP_PASSWORD"}}'` -> returns `workflowId`.
2. Grant the alias to that workflow. When the user pasted the password in chat: `teable secret set --key IMAP_PASSWORD --value <password> --grant automation:<workflowId>`. Otherwise use `request_credential` (credentialType `secret`, resourceType `automation`, resourceId `<workflowId>`, alias `IMAP_PASSWORD`); if it returns a different alias, rerun setup-trigger with `--workflow-id <workflowId>` and that alias (config merges).
3. `teable automation test-node` - a `Secret <ALIAS> is not granted` error means step 2 was skipped.

Required: `emailReceivedConfig.connectionType`, `emailReceivedConfig.host`, `emailReceivedConfig.user`

**Output Variables:**
- `emails` - Array of received email objects (see fields below)
- `emailCount` - Number of emails received in this batch
- `triggerTime` - ISO timestamp when the trigger fired

Each entry in `emails[]`:
- `from` - Sender email address
- `fromName` - Sender display name (may be empty)
- `to` - Comma-separated recipient addresses
- `cc` - Comma-separated CC addresses
- `subject` - Email subject
- `date` - ISO timestamp from the email's Date header
- `messageId` - RFC 5322 Message-ID
- `body` - Plain text or HTML body (depends on trigger config `bodyFormat`)
- `priority` - `"high"` | `"normal"` | `"low"`
- `inReplyTo` - Message-ID this email is replying to (empty if not a reply)
- `attachments[]` - `{ filename, contentType, size, fileUrl }`

⚠️ **`fileUrl` is a short-lived signed URL** (lifetime varies by storage provider — minutes to hours). Download any attachments you need within the same script run; do not cache `fileUrl` for later use.

### 9. connectorEvent - When Connector Event Received
Triggers when a connected third-party app (GitHub, Gmail, Slack...) reports an event. The subscription runs on the user's own connection to that app, bound to the workflow as a credential grant.

**Five-step flow:**
1. `composio_search_events` with no `toolkit` → the apps that publish events, each with `connected` telling whether the user has already connected it.
2. Call it with `toolkit` to see the event types and their parameters; add `eventType` to get that event's `payloadFields` (the fields of `event`).
3. `setup-automation-trigger` with `triggerType: "connectorEvent"` and `connectorEventConfig`, without an account. Then `request_credential` (credentialType `connection`, provider = the toolkit slug, resourceType `automation`, resourceId = that workflow) puts a card in front of the user, and `setup-automation-trigger` is called again with `connectorEventConfig.alias` set to the `alias` it returns. Until then the workflow cannot listen or be activated.
4. Optional: if the user can trigger the event now, `test-automation-node` on the trigger listens for the next event (up to 30 minutes), which becomes its test result by itself (needed to test later nodes); once it has one, testing runs on it. Otherwise write the script from `payloadFields` (`const { event } = input['<triggerId>']`).
5. `activate-automation` with `method: "activate"` to publish. The subscription is created on activation; `get-automation` reports it as `trigger.eventSource.status` (`pending` → `active`, or `disconnected`).

`disconnected` means the account is lost: ask the user to reconnect the app in Settings → Integrations, or bind another connection with `request_credential` and write back `connectorEventConfig.alias`.

```json
{
  "triggerType": "connectorEvent",
  "connectorEventConfig": {
    "toolkit": "github",
    "eventType": "GITHUB_ISSUE_ADDED_EVENT",
    "alias": "github_connection",
    "eventConfig": { "owner": "teableio", "repo": "teable" }
  }
}
```

Required: `toolkit`, `eventType`. The account is `alias`, a connection already granted to this workflow — what `request_credential` returned, or one `get-automation` reports as the stored binding; omit it to save the trigger first and bind later.

**`eventConfig`:** its keys are not fixed. They come from the event type's own `config` JSON schema, which `composio_search_events` returns as `params` (name, type, description, enum) with the mandatory ones listed in `requiredParams`. A missing required parameter is rejected before anything is created. On an update `eventConfig` is merged into the stored one key by key, so a partial change keeps the rest.

**`kind`:**
- `webhook` — the app pushes the event, so it arrives within seconds.
- `poll` — Teable asks the app on a schedule, so the event can arrive **minutes late**. Do not build anything time-critical on a poll event type.

⚠️ **`highVolume`:** an event type that takes no required parameter fires for *everything* on the connected account (every repository, every channel). Warn the user before setting one up, and prefer an event type that can be narrowed with `eventConfig`.

**Output Variables:**
- `event` - The event payload exactly as the app sent it
- `eventType` - The event type slug that fired
- `account` - The connected account the event came from
- `occurredAt` - ISO timestamp of the event as Composio recorded it: close to the source for `webhook`, up to one poll interval late for `poll`. Events can arrive out of order; when order matters, compare it with the last event time stored on the record and skip older events.
- `receivedAt` - ISO timestamp of when Teable received it
- `eventId` - Provider event id, useful for de-duplication
