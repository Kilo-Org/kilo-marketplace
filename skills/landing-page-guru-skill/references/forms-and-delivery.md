# Forms and delivery

A form is a journey from intent to an accepted request and its promised next step.
Specify its operational contract before making it look successful.

## Define the contract

Use the bundled integration template/schema. Record mode (`unconnected`, `test`,
or `live`), fields and purposes, public destination/configuration reference,
response meanings, retry behavior, success mode, delivery visibility, events, and
privacy decisions. Store secret variable names only, never values.

If no endpoint exists, keep the page useful with an explicitly unconnected form
or the user's approved alternative action. Do not simulate real acceptance. A
demo can simulate acceptance only when the visitor sees that it is a demo.

## Controls and states

- Collect only fields needed to fulfill or qualify this request; justify extras.
- Give every field a visible associated label, useful autocomplete/inputmode,
  required indication, and instructions before errors occur.
- Preserve entered values after rejection/network failure; attach field errors
  and provide a perceivable status region. Focus a relevant error when needed.
- Prevent duplicate clicks while pending. Restore the action after recoverable
  failure. Avoid permanently disabling valid autofill or paste.
- Validate on the server as well as in the browser. Native email validation is
  useful syntax checking, not proof that an address can receive mail.
- Use proportionate server-side abuse controls. Fast autofill alone is not spam.
  If using challenge tokens, validate them server-side with current documentation.

## Response semantics

Separate these states: validation rejected; request in flight; outcome unknown
after a timeout; accepted by backend; stored; notification queued/sent; received.
Only claim the stage that is observable. A 2xx HTTP status alone may not mean
application acceptance: check the documented response body too.

Retain an idempotency identifier for a retry of the same logical submission if
the backend supports it. A timeout may have happened after acceptance. Without
retry safety, explain uncertainty instead of issuing blind repeated submissions.
Duplicate acceptance must not produce a second conversion or lead.

In-place confirmation and redirect are both valid. For redirects, never infer a
new submission from visiting or reloading the success URL. Associate conversion
with confirmed acceptance and deduplicate by a non-personal identifier.

## Delivery and promises

Confirm the intended destination and owner. Test delivery only in an authorized
test destination. An intercepted browser response proves neither storage nor
notification. A recipient's receipt is a separate observation from “email queued.”
Surface failures after acceptance so the lead is not silently lost.

For downloads, verify the actual resource, type, link, and permissions. Do not
promise “check your inbox” if only an on-page download exists. Use authenticated
sending appropriate to the real email setup; do not invent a universal requirement
that every customer configure their own sending domain.

## Focused helper

`scripts/test-form-flow.mjs --help` describes the optional browser helper. It
intercepts the configured endpoint and exercises required-field validation,
acceptance, rejection, duplicate response, simulated transport timeout, and retry.
It blocks other mutations. It does not validate the backend, actual delivery,
all accessibility requirements, or consent behavior. Supplement it with available
manual/browser checks and record unsupported tests honestly.

Use `assets/browser-form-template.json` as the adapter shape inside the contract's
`verification.browser` field. Synthetic values belong only in test inputs. Keep
real personal data out of fixtures, screenshots, and reports.
