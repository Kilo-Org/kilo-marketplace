# Browser SDK persistence

Use the narrowest storage surface that satisfies the product:

| Need | Namespace | Access |
|---|---|---|
| Small private app state | `AiPass.data` | Current user + current app |
| Private files | `AiPass.files` | Current user + current app |
| Intentional workflow across apps | `AiPass.shared` | Current user + explicitly granted apps |

All methods authenticate at call time. A signed-out call opens the official SDK login modal and
resumes after OAuth. Do not gate the action with `AiPass.isAuthenticated()` or build a custom login
screen. A dismissed modal rejects with `error.code === 'AUTH_REQUIRED'`.

Never store passwords, OAuth tokens, API keys, cookies, wallet credentials, or other secrets.

## Private JSON and files

```javascript
const state = await AiPass.data.get(); // {} on first use
state.drafts = state.drafts || [];
await AiPass.data.set(state, { ifRevision: AiPass.data.revision });

const saved = await AiPass.files.upload(file, { name: file.name });
const blob = await AiPass.files.download(saved.id);
const url = await AiPass.files.getUrl(saved.id);
URL.revokeObjectURL(url);
```

`AiPass.data` is one whole JSON document per `(user, app)`, capped at 1 MB and approximately 30
writes/minute. Conditional writes reject stale revisions. `AiPass.files` permits 10 MB/file, 50 MB
total, and 100 files per user/app. Downloads are authenticated `Blob` responses without permanent
public URLs. Both are free and do not spend wallet balance.

## User-owned shared vaults

```javascript
const vault = await AiPass.shared.create('Campaign autumn');
await AiPass.shared.records.set(vault.id, 'request:hero', { prompt });

await AiPass.shared.grant(vault.id, {
  appRef: 'oauth:image-app-client-id',
  access: 'CONTRIBUTE'
});

// The granted app, signed in as the same user:
const available = await AiPass.shared.list();
const request = await AiPass.shared.records.get(vault.id, 'request:hero');
const image = await AiPass.shared.files.upload(vault.id, generatedBlob, { name: 'hero.png' });
await AiPass.shared.records.set(vault.id, 'result:hero', { fileId: image.id });
```

The SDK resolves the target app and displays a contextual AI Pass confirmation before writing a
grant. Do not replace this with silent access. Only the creator app can grant/revoke access or
delete the vault.

App references:

- `oauth:{clientId}` for an external OAuth SDK app;
- `app:{slug}` for a catalog app;
- `space:{handle}/{slug}` for a Space app.

Permissions:

- `READ`: list/read JSON and list/download files.
- `CONTRIBUTE`: read and add new record keys/files; no replace/delete.
- `READ_WRITE`: read/add/replace/delete records/files.

Prefer `CONTRIBUTE` for request/result handoffs. It permits a new `result:*` key without allowing
the collaborator to overwrite the source `request:*` key.

## Method map

```text
AiPass.shared.list()
AiPass.shared.create(name)
AiPass.shared.get(vaultId)
AiPass.shared.remove(vaultId)
AiPass.shared.resolveApp(appRef)
AiPass.shared.listGrants(vaultId)
AiPass.shared.grant(vaultId, { appRef, access })
AiPass.shared.revoke(vaultId, grantId)

AiPass.shared.records.list/get/set/remove
AiPass.shared.files.list/upload/download/getUrl/remove
```

Record methods take `vaultId` first; file methods do the same. `records.set` accepts optional
`{ ifRevision }`. Record keys are 1-128 characters containing letters, numbers, `.`, `_`, `:`, and
`-`. Store a returned file ID in a record when another app needs to discover a shared file.

## Limits and security invariants

- 20 vaults/user, 500 records/vault, 1 MB combined JSON/vault, and 20 grants/vault.
- 10 MB/file, 50 MB files/vault, and 100 files/vault.
- Every operation is constrained to the same signed-in user.
- Shared access never opens another user's data or the creator app's private namespace.
- Shared files remain private authenticated downloads.
- Storage is free and does not spend AI balance.

Verify signed-out modal/resume, dismissal, stale revisions, least-privilege permission failures,
revocation, another-user denial, and object-URL cleanup. Keep an existing host database authoritative
when server-side queries, compliance controls, backups, or workers need the data.
