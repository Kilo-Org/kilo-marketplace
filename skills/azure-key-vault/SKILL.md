---
name: "azure-key-vault"
description: "Guidance for Azure Key Vault — securely storing and managing secrets, keys, and certificates with RBAC, network isolation, managed identity access, soft delete / purge protection, and rotation. Covers when to use standard Key Vault vs Managed HSM (FIPS 140-3 Level 3), one-vault-per-app blast radius principle, and Key Vault references in App Service / Functions. WHEN: Azure Key Vault, store secrets, manage certificates, encryption keys, secret rotation, Key Vault RBAC, purge protection, soft delete, private endpoint Key Vault, managed identity access secrets, Managed HSM, Key Vault references, BYOK CMK. DO NOT USE for certificate authority design (use pki-design), entra app credentials only (use entra-id), or PaaS networking topology (use azure-network-security-design)."
metadata:
  category: data
  source:
    repository: "https://github.com/vinayaklatthe/microsoft-security-skills"
    path: "skills/azure-key-vault"
    license_path: "LICENSE"
---

# Azure Key Vault

Azure Key Vault centrally and securely stores **secrets, keys, and certificates**, providing
RBAC-based access control, network isolation, logging, and lifecycle automation - so
applications never embed credentials and crypto material has a managed lifecycle.

## When to use
Managing application secrets, encryption keys (including customer-managed keys / BYOK), and
TLS certificates. Use this skill to pick standard vs Managed HSM, design access, and plan
rotation.

**Do not use this skill** for CA design (`pki-design`), Entra app credentials only
(`entra-id`), or PaaS networking topology (`azure-network-security-design`).

## Pick the vault type and access model

| Requirement | Choice | Notes |
|---|---|---|
| Application secrets, TLS certs, software-protected keys | **Standard Key Vault** | Default; FIPS 140-2 Level 2 |
| Single-tenant HSM with FIPS 140-3 Level 3 keys (CMK, root CA) | **Managed HSM** | Regulated workloads |
| Per-app, per-environment isolation | **One vault per app per environment** | Limits blast radius |
| App reading secrets at runtime | **Managed identity + RBAC** (Key Vault Secrets User) | No secrets in code |
| App Service / Functions secret in config | **Key Vault references** in app settings | No code change |
| Customer-managed key for Storage / SQL | Key in Key Vault (or HSM) + identity grant | Rotate independently |

> **Rule of thumb:** **one vault per app per environment** (dev / test / prod). Don't share a
> vault across apps - a compromise of one app's identity reads all the others' secrets. Use
> Managed HSM only when the regulator or CMK boundary requires FIPS 140-3 Level 3.

## Approach

1. **Use Azure RBAC for the data plane** — Switch the vault to **RBAC permission model** (not
   legacy access policies). Assign least-privilege roles (`Key Vault Secrets User`,
   `Key Vault Crypto User`) to **managed identities**, not user accounts.
   *Verify: vault `enableRbacAuthorization = true`; no users with `Key Vault Administrator`
   in prod.*

2. **App access via managed identity + Key Vault references** — App authenticates with a
   system-assigned or user-assigned managed identity, fetches secrets at runtime.
   For App Service / Functions, use **Key Vault references** in app settings -
   `@Microsoft.KeyVault(SecretUri=...)` - no SDK code change.
   *Verify: source code contains no plaintext secrets; managed identity has only the
   secrets role on the target vault.*

3. **Enable soft delete + purge protection** — Soft delete is on by default; **turn on
   purge protection** to make accidental or malicious key deletion non-recoverable for
   90 days. Required for CMK and most compliance scenarios.
   *Verify: `softDeleteRetentionInDays >= 7`; `enablePurgeProtection = true`.*

4. **Restrict network access** — For sensitive vaults, **disable public network access** and
   use **private endpoint** in the workload VNet. Firewall the rest with service tags or
   selected networks.
   *Verify: `publicNetworkAccess = Disabled`; private endpoint resolves; public IP test
   from internet = blocked.*

5. **One vault per app per environment** — Per-app blast radius. Cross-app reads are then a
   role grant, audited. Don't lump secrets into a shared vault.

6. **Automate rotation + monitor expiry** — Set expiry on secrets / certs; use **rotation
   policies** for certificate auto-renewal from issuer; for secrets, use Event Grid → Logic
   App / Function to rotate at the source and update the secret.
   *Verify: no secret in production has a NULL expiry; alerts fire 60 days before any cert
   or secret expires.*

7. **Monitor + Defender** — Enable diagnostic logs to Log Analytics; turn on **Defender for
   Key Vault** for anomalous access detection.

## Guardrails
- **One vault per app per environment limits blast radius and simplifies access control.**
  Shared vaults are an over-permission anti-pattern.
- **Purge protection is irreversible once on - required for CMK and many compliance
  scenarios.** Turn it on knowingly.
- **Never store secrets in source / config; use managed identity + Key Vault references.**
  Code-stored secrets leak via repo, logs, env-var dumps.
- **Disable public network access for sensitive vaults.** Open-to-internet Key Vault is a
  brute-force / credential-spray target.
- **RBAC, not access policies.** RBAC is the modern model with proper inheritance and
  PIM-eligible roles.
- **Don't grant `Key Vault Administrator` to apps.** Apps need read on secrets / keys, not
  admin.

## Common anti-patterns
- **"Shared 'enterprise' Key Vault for all apps"** - Compromise of one app reads everyone's
  secrets. Per-app per-environment.
- **"Access policies because we've always used them"** - Legacy; harder to audit. Use RBAC.
- **"No purge protection - we might need to delete"** - First malicious / accidental purge
  = data loss. Turn it on; deal with the irrevocability.
- **"Public network access on for convenience"** - Internet exposure. Private endpoint
  + firewall.
- **"Secrets in App Service application settings as plaintext"** - Visible to anyone with
  config read. Use Key Vault references.
- **"No expiry / no rotation"** - Long-lived secrets are a perpetual liability. Expiry +
  rotation policy.
- **"Same vault for app + CA root key"** - Mix of blast radii. CA / HSM keys in **Managed
  HSM**, separate from app secret vault.

## Example prompts
- `Set up Azure Key Vault with RBAC, purge protection, and a private endpoint.`
- `Configure an App Service to read secrets via managed identity and Key Vault references.`
- `When should I use Managed HSM instead of standard Key Vault?`
- `Plan one-vault-per-app-per-environment for our microservices estate.`
- `Automate certificate rotation in Key Vault with a 60-day expiry alert.`
- `Review my Key Vault access model for least privilege.`

## Microsoft Learn
- Key Vault overview: https://learn.microsoft.com/azure/key-vault/general/overview
- Security features: https://learn.microsoft.com/azure/key-vault/general/security-features
- RBAC guide: https://learn.microsoft.com/azure/key-vault/general/rbac-guide
- Soft delete + purge protection: https://learn.microsoft.com/azure/key-vault/general/soft-delete-overview
- Private endpoints: https://learn.microsoft.com/azure/key-vault/general/private-link-service
- Key Vault references in App Service: https://learn.microsoft.com/azure/app-service/app-service-key-vault-references
- Managed HSM: https://learn.microsoft.com/azure/key-vault/managed-hsm/overview
- Defender for Key Vault: https://learn.microsoft.com/azure/defender-for-cloud/defender-for-key-vault-introduction
