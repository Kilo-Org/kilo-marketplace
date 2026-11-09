# Secrets Guide

Use `teable secret` for credentials consumed by a specific app or automation. Credentials are personal and write-only; resources receive them through grants under an environment-variable alias. Use [env-guide.md](env-guide.md) only for personal chat environment variables.

## Credential and grant workflow

1. Run `secret list` without a resource to find secrets and OAuth connections you own; values are never returned.
2. For a new plaintext credential, store and grant it atomically with `secret set --grant`. For an existing secret or OAuth connection, use `secret grant`.
3. Run `secret list --resource app:appXXX` or `--resource automation:wflXXX` to verify bindings and find unbound placeholders expected by resource code.
4. Revoke a grant when only one resource should lose access. Delete the secret only when every grant should lose it.

Resource identifiers must use `app:<id>` or `automation:<id>`. Aliases become `process.env.ALIAS` for secrets and must be uppercase identifiers. Prefer the resource's unbound placeholder name when one exists.

## Safety rules

- Treat values as irretrievable after writing; retain them in the user's password manager or source vault.
- A duplicate personal key fails safely. Rotate only when replacement is intentional: every existing grant sees the new value.
- An existing alias is not rebound unless replacement is explicitly requested. Inspect resource bindings before replacing it.
- `secret revoke` keeps the credential and its other grants. `secret delete` removes the credential and **all** grants; verify the secret ID and impacted resources first.
- Granting later can enter a resource approval flow; use atomic set-and-grant when creating a credential specifically for one resource.
