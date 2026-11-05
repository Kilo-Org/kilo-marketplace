# Privacy and security for the actual page

Load this when the task collects data, embeds external content, handles credentials,
or adds tracking. Scope it to the implementation and audience instead of adding a
generic compliance questionnaire to every copy edit.

## Establish the real configuration

Record audience regions, field purposes, recipient/processor, retention owner and
decision, actual trackers/storage, permission category, and unresolved requirements.
Use the user's policy where supplied. Do not invent a company address, retention
period, legal basis, certification, or claim of legal compliance.

Keep fulfilling an inquiry distinct from subscribing someone to unrelated
marketing. Explain the data use near collection in language consistent with the
actual processing. Provide the real notice link when available; mark missing policy
configuration rather than generating a fake link or publishing boilerplate as fact.

Requirements and exemptions vary by audience and implementation. Consult current
primary regulator guidance for a concrete legal decision, and seek the appropriate
owner's input where unresolved. Avoid universal claims that every analytics use
requires consent or that “first party” automatically means exempt.

## Enforce configured behavior

If a category requires permission, don't initialize its storage/requests before
permission. Exercise refusal, grant, and withdrawal; remove or stop subsequent
collection as the configuration requires. A decorative banner that does not control
tracking is not a completed integration.

Use allowlisted analytics properties. Never export field values, session tokens,
raw URLs containing personal data, or secrets into analytics or test reports. Use
synthetic data and isolated fixtures when verifying. Review captured artifacts
before sharing them.

## Keep the boundary on the server

Validate types, lengths, allowed fields, content, and abuse controls on the server.
Keep secrets in appropriate server configuration, never in generated HTML, browser
JavaScript, query strings, screenshots, or a skill file. Escape rendered user input;
do not inject it as HTML. Apply the existing application's CSRF/origin/auth rules
where relevant instead of weakening them to make a form work.

An unknown endpoint or unavailable backend means server checks are `not-tested`.
Don't claim a secure or compliant system from a frontend demo. Consult the current
[OWASP validation guidance](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
for implementation details relevant to the selected stack.
