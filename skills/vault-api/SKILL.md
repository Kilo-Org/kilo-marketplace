---
name: vault-api
description: >-
  Use when working with HashiCorp Vault REST API — health checks, init/unseal,
  auth login, KV read/write, policy management, token operations. Covers
  endpoints, auth methods, curl examples.
metadata:
  category: development
  source:
    repository: 'https://github.com/Aidas-dev/k8s-agent-skills'
    path: skills/vault-api
    license_path: LICENSE
    commit: 32268017f64a968e68842387e61f02caeb02c876
---

# Vault API

## Overview

Vault exposes a RESTful JSON API on port 8200. All requests include `X-Vault-Token` header for authenticated endpoints. Unauthenticated endpoints (health, init) need no token.

**Base URL:** `http://vault.vault:8200` (in-cluster) or `https://vault.kubexa.tech` (external via Gateway).

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
# Login with K8s SA token
SA_JWT=$(kubectl create token my-sa -n my-ns)
curl -s http://vault.vault:8200/v1/auth/kubernetes/login \
  -d "{\"role\":\"my-role\",\"jwt\":\"$SA_JWT\"}"
# Returns: {"auth":{"client_token":"hvs...","policies":["my-policy"]}}
```

### KV Secrets (v2)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/{mount}/data/{path}` | Read secret |
| `PUT` | `/v1/{mount}/data/{path}` | Create/update secret |
| `DELETE` | `/v1/{mount}/data/{path}` | Delete latest version |
| `GET` | `/v1/{mount}/metadata/{path}` | Read metadata (versions, timestamps) |
| `POST` | `/v1/{mount}/delete/{path}` | Delete all versions |
| `POST` | `/v1/{mount}/undelete/{path}` | Undelete |

```bash
# Write a secret
curl -s http://vault.vault:8200/v1/secret/data/myapp \
  -H "X-Vault-Token: $VAULT_TOKEN" \
  -d '{"data":{"password":"s3cret!"}}'

# Read a secret
curl -s http://vault.vault:8200/v1/secret/data/myapp \
  -H "X-Vault-Token: $VAULT_TOKEN"
# Returns: {"data":{"data":{"password":"s3cret!"},"metadata":{...}}}

# List secrets at a path
curl -s http://vault.vault:8200/v1/secret/metadata/myapp \
  -H "X-Vault-Token: $VAULT_TOKEN" \
  | jq '.data.keys'
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
curl -s http://vault.vault:8200/v1/sys/policies/acl/myapp \
  -X PUT \
  -H "X-Vault-Token: $VAULT_TOKEN" \
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

# Take snapshot
curl -s http://vault.vault:8200/v1/sys/storage/raft/snapshot \
  -H "X-Vault-Token: $VAULT_TOKEN" \
  -o vault-snapshot.snap
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
curl -s http://vault.vault:8200/v1/sys/health | jq .initialized

# Detailed status
curl -s http://vault.vault:8200/v1/sys/seal-status | jq '.sealed, .t, .n, .progress'
```

## Common Mistakes

- **KV v2 path includes `data/` prefix.** For KV v2 engine mounted at `secret`, the read path is `/v1/secret/data/myapp`, not `/v1/secret/myapp`. The latter returns a 404.
- **Health endpoint returns non-200 for sealed/standby.** A 503 (sealed) is NOT an error — it's expected after restart. Check `initialized` and `sealed` fields in the response body, not the HTTP status alone.
- **Token in URL is stripped by proxies.** Use `X-Vault-Token` header, not `?token=` query param. Proxies and load balancers may log or strip query params.
- **Kubernetes auth needs SA token with right audience.** The `vault` audience must be configured in the SA or the default token may not be accepted. Use `kubectl create token` with `--audience=vault` for explicit audience.
- **`list` capabilities for metadata listing.** Reading `/v1/secret/metadata/` (to list keys) requires `list` capability at that path, not `read`. Without it, the response is empty.
- **Raft join after unseal.** A sealed node cannot join the Raft cluster. Always unseal before `raft join`. The joining node will sync data from the leader.
- **Snapshot restore requires same cluster size.** Raft snapshots can only be restored to a cluster with the same number of peers. Adding/removing nodes after restore may fail.
