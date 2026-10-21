# Personal Environment Variables Guide

Use `teable env` only for personal environment variables used by chat sessions. For credentials needed by an app or automation, use [secret-guide.md](secret-guide.md) to grant a write-only secret or OAuth connection to that resource.

The scope defaults to `user`; app and automation scopes are not supported. Env commands do not use project context.

## Workflow and safety

- `env list` finds variable IDs; values may be sensitive, so do not echo them unnecessarily.
- `env set` upserts by key. Use it when creating a variable or intentionally replacing its value.
- `env update` targets an existing variable ID when changing its value or description.
- `env delete` is destructive; verify the ID and consumers first.

Keys must match `^[A-Z][A-Z0-9_]{0,63}$` so code can read them as `process.env.KEY`. Never confuse these custom values with automation runtime variables such as `AUTOMATION_TOKEN` and `PUBLIC_ORIGIN`, which are built in.
