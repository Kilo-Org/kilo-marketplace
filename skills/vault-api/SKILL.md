---
name: "vault-api"
description: "Use when working with HashiCorp Vault REST API — health checks, init/unseal, auth login, KV read/write, policy management, token operations. Covers endpoints, auth methods, curl examples."
metadata:
  category: data
  source:
    repository: "https://github.com/Aidas-dev/k8s-agent-skills"
    path: "skills/vault-api"
    license_path: "LICENSE"
---

# Vault API

## Overview

Vault exposes a RESTful JSON API on port 8200. All requests include `X-Vault-Token` header for authenticated endpoints. Unauthenticated endpoints (health, init) need no token.

**Base URL:** `https://vault.vault:8200` (in-cluster with TLS) or `https://vault.example.invalid` (synthetic external example). Validate the CA and hostname; do not disable TLS verification in production.

## API Endpoints

### System

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/v1/sys/health` | Cluster health (see status codes below) | No |
| `GET` | `/v1/sys/seal-status` | Seal status | No |
| `PUT` | `/v1/sys/init` | Initialize cluster | No |
| `PUT` | `/v1/sys/unseal` | Unseal (submit key share) | No |
| `GET` | `/v1/sys/leader` | Current leader info | No |

**Health status codes:**

| Code | Meaning |
|------|---------|
| `200` | Active, unsealed |
| `429` | Standby, unsealed |
| `472` | Disaster Recovery secondary (enterprise) |
| `473` | Performance standby (enterprise) |
| `501` | Not initialized |
| `503` | Sealed |

### Auth (Kubernetes)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/auth/kubernetes/login` | Login with service account JWT |

```bash
# Login with a K8s SA token without putting the JWT in curl's argument list.
VAULT_ADDR="https://vault.vault:8200"
umask 077
LOGIN_REQUEST=$(mktemp)
LOGIN_RESPONSE=$(mktemp)
VAULT_CURL_CONFIG=$(mktemp)
trap 'rm -f "$LOGIN_REQUEST" "$LOGIN_RESPONSE" "$VAULT_CURL_CONFIG"' EXIT

SA_JWT=$(kubectl create token my-sa -n my-ns --audience=vault)
printf '{"role":"my-role","jwt":"%s"}' "$SA_JWT" > "$LOGIN_REQUEST"
unset SA_JWT
curl --fail --silent --show-error \
  --request POST \
  --data-binary @"$LOGIN_REQUEST" \
  --output "$LOGIN_RESPONSE" \
  "$VAULT_ADDR/v1/auth/kubernetes/login"

VAULT_TOKEN=$(jq -r '.auth.client_token' "$LOGIN_RESPONSE")
printf 'header = "X-Vault-Token: %s"\n' "$VAULT_TOKEN" > "$VAULT_CURL_CONFIG"
unset VAULT_TOKEN

# Inspect only non-secret login metadata.
jq '{policies: .auth.policies, lease_duration: .auth.lease_duration}' "$LOGIN_RESPONSE"
rm -f "$LOGIN_REQUEST" "$LOGIN_RESPONSE"
# Keep $VAULT_CURL_CONFIG mode 0600 and delete it when the session ends.
```

### KV Secrets (v2)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/{mount}/data/{path}` | Read secret |
| `PUT` | `/v1/{mount}/data/{path}` | Create/update secret |
| `DELETE` | `/v1/{mount}/data/{path}` | Soft-delete the latest version |
| `GET` | `/v1/{mount}/metadata/{path}` | Read metadata (versions, timestamps) |
| `POST` | `/v1/{mount}/delete/{path}` | Soft-delete specified versions |
| `POST` | `/v1/{mount}/undelete/{path}` | Restore specified soft-deleted versions |
| `PUT` | `/v1/{mount}/destroy/{path}` | Permanently destroy specified versions |
| `DELETE` | `/v1/{mount}/metadata/{path}` | Permanently delete all versions and metadata |

Use the mode-0600 `$VAULT_CURL_CONFIG` created during login so the token does not appear in process arguments. Build secret payloads from a masked prompt or trusted secret provider, and do not print read responses to the terminal.

```bash
# Write a secret from a masked prompt and mode-0600 request file.
SECRET_VALUE_FILE=$(mktemp)
SECRET_REQUEST=$(mktemp)
read -r -s -p "Secret value: " SECRET_VALUE
printf '\n'
printf '%s' "$SECRET_VALUE" > "$SECRET_VALUE_FILE"
unset SECRET_VALUE
jq -n --rawfile password "$SECRET_VALUE_FILE" \
  '{data: {password: $password}}' > "$SECRET_REQUEST"
rm -f "$SECRET_VALUE_FILE"
curl --fail --silent --show-error \
  --config "$VAULT_CURL_CONFIG" \
  --request PUT \
  --data-binary @"$SECRET_REQUEST" \
  "$VAULT_ADDR/v1/secret/data/myapp" >/dev/null
rm -f "$SECRET_REQUEST"

# Read to a protected file; expose only metadata in logs.
SECRET_RESPONSE=$(mktemp)
curl --fail --silent --show-error \
  --config "$VAULT_CURL_CONFIG" \
  --output "$SECRET_RESPONSE" \
  "$VAULT_ADDR/v1/secret/data/myapp"
jq '.data.metadata' "$SECRET_RESPONSE"
rm -f "$SECRET_RESPONSE"

# List keys (LIST is the Vault-specific method for this endpoint).
curl --fail --silent --show-error \
  --config "$VAULT_CURL_CONFIG" \
  --request LIST \
  "$VAULT_ADDR/v1/secret/metadata/myapp" \
  | jq '.data.keys'
```

**Destructive secret operations:** soft deletion is recoverable only while the version has not been destroyed and metadata still exists. Before any destroy, metadata delete, v1 delete, or secrets-engine disable, read the exact mount/path/version metadata, check dependencies and retention/legal-hold requirements, verify an approved recovery source or Raft snapshot, and require typed confirmation of the full target. Permanent destruction cannot be undone. Keep destructive curl commands out of reusable scripts unless they implement that guard.

```bash
# Guarded permanent-destroy example. Do not set these values until recovery and
# retention checks are complete and the exact target has been approved.
umask 077
MOUNT="secret"
SECRET_PATH="myapp"
VERSION="<VERSION_NUMBER>"
if [[ ! "$MOUNT" =~ ^[A-Za-z0-9_-]+$ \
   || ! "$SECRET_PATH" =~ ^[A-Za-z0-9_./-]+$ \
   || ! "$VERSION" =~ ^[0-9]+$ ]]; then
  printf '%s\n' "Invalid mount, path, or version; aborted."
  exit 1
fi

curl --fail --silent --show-error \
  --config "$VAULT_CURL_CONFIG" \
  "$VAULT_ADDR/v1/$MOUNT/metadata/$SECRET_PATH" \
  | jq --arg version "$VERSION" '.data.versions[$version]'
read -r -p "Type DESTROY ${MOUNT}/${SECRET_PATH} VERSION ${VERSION}: " CONFIRMATION
if [ "$CONFIRMATION" = "DESTROY ${MOUNT}/${SECRET_PATH} VERSION ${VERSION}" ]; then
  DESTROY_REQUEST=$(mktemp)
  jq -n --argjson version "$VERSION" '{versions: [$version]}' > "$DESTROY_REQUEST"
  curl --fail --silent --show-error \
    --config "$VAULT_CURL_CONFIG" \
    --request PUT \
    --data-binary @"$DESTROY_REQUEST" \
    "$VAULT_ADDR/v1/$MOUNT/destroy/$SECRET_PATH" >/dev/null
  rm -f "$DESTROY_REQUEST"
else
  printf '%s\n' "Aborted; target confirmation did not match."
fi
```

### KV Secrets (v1)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/{mount}/{path}` | Read secret |
| `PUT` | `/v1/{mount}/{path}` | Create/update secret |
| `DELETE` | `/v1/{mount}/{path}` | Delete secret |

### Policies

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/sys/policies/acl` | List ACL policies |
| `GET` | `/v1/sys/policies/acl/{name}` | Read policy |
| `PUT` | `/v1/sys/policies/acl/{name}` | Create/update policy |
| `DELETE` | `/v1/sys/policies/acl/{name}` | Delete policy |

```bash
# Create read-only policy for myapp
curl -s $VAULT_ADDR/v1/sys/policies/acl/myapp \
  -X PUT \
  --config "$VAULT_CURL_CONFIG" \
  -d '{"policy":"path \"secret/data/myapp/*\" {capabilities=[\"read\",\"list\"]}"}'
```

### Token

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/auth/token/create` | Create token |
| `POST` | `/v1/auth/token/create-orphan` | Create orphan token |
| `GET` | `/v1/auth/token/lookup-self` | Validate/lookup own token |
| `POST` | `/v1/auth/token/renew-self` | Renew own token |
| `POST` | `/v1/auth/token/revoke-self` | Revoke own token |

### Auth Methods

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/sys/auth` | List enabled auth methods |
| `POST` | `/v1/sys/auth/{type}` | Enable auth method |
| `DELETE` | `/v1/sys/auth/{path}` | Disable auth method |

### Secrets Engines

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/sys/mounts` | List enabled secret engines |
| `POST` | `/v1/sys/mounts/{path}` | Enable secret engine (type: kv-v2, kv, transit, etc.) |
| `DELETE` | `/v1/sys/mounts/{path}` | Disable/delete secret engine |

### Raft

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/sys/storage/raft/join` | Join Raft cluster |
| `GET` | `/v1/sys/storage/raft/configuration` | List Raft peers |
| `POST` | `/v1/sys/storage/raft/snapshot` | Take Raft snapshot |

```bash
# Join Raft cluster
curl -s http://127.0.0.1:8200/v1/sys/storage/raft/join \
  -X POST \
  -d '{"leader_api_addr":"http://vault-0.vault-internal:8200"}'

# Take snapshot to a protected file
umask 077
curl --fail --silent --show-error \
  --config "$VAULT_CURL_CONFIG" \
  --output vault-snapshot.snap \
  "$VAULT_ADDR/v1/sys/storage/raft/snapshot"
```

## Auth Methods Summary

| Method | Endpoint Mount | Use Case |
|--------|---------------|----------|
| Kubernetes | `/v1/auth/kubernetes/login` | In-cluster pods via SA JWT |
| Token | `/v1/auth/token/create` | Root token, periodic tokens |
| AppRole | `/v1/auth/approle/login` | Machine-to-machine (w/ secretId) |
| Userpass | `/v1/auth/userpass/login` | Human users |
| LDAP | `/v1/auth/ldap/login` | Enterprise directory integration |
| JWT/OIDC | `/v1/auth/jwt/login` | External OIDC providers |
| Cert | `/v1/auth/cert/login` | mTLS client certificates |

## Health Check Examples

```bash
# Quick health
curl -s $VAULT_ADDR/v1/sys/health | jq .initialized

# Detailed status
curl -s $VAULT_ADDR/v1/sys/seal-status | jq '.sealed, .t, .n, .progress'
```

## Common Mistakes

- **KV v2 path includes `data/` prefix.** For KV v2 engine mounted at `secret`, the read path is `/v1/secret/data/myapp`, not `/v1/secret/myapp`. The latter returns a 404.
- **Health endpoint returns non-200 for sealed/standby.** A 503 (sealed) is NOT an error — it's expected after restart. Check `initialized` and `sealed` fields in the response body, not the HTTP status alone.
- **Never put a token in the URL or curl arguments.** Use the `X-Vault-Token` header through a mode-0600 curl config file. Query strings, shell history, and process listings can expose credentials.
- **Kubernetes auth needs SA token with right audience.** The `vault` audience must be configured in the SA or the default token may not be accepted. Use `kubectl create token` with `--audience=vault` for explicit audience.
- **`list` capabilities for metadata listing.** Reading `/v1/secret/metadata/` (to list keys) requires `list` capability at that path, not `read`. Without it, the response is empty.
- **Raft join after unseal.** A sealed node cannot join the Raft cluster. Always unseal before `raft join`. The joining node will sync data from the leader.
- **Snapshot restore requires same cluster size.** Raft snapshots can only be restored to a cluster with the same number of peers. Adding/removing nodes after restore may fail.
