---
name: "aws-cognito-admin"
description: "Cognito user pool administration — look up users, confirm accounts, reset passwords, update custom attributes, disable/enable accounts, and describe pool configuration. Discovers user pools at runtime. Trigger on \"look up a user\", \"Cognito\", \"reset password\", \"disable an account\", \"fix subscription\", or /aws-cognito-admin."
metadata:
  category: data
  source:
    repository: "https://github.com/monahand1023/claude-code-skills"
    path: "aws-cognito-admin"
    license_path: "LICENSE"
---

# AWS Cognito Admin

Perform Cognito user pool administration without hardcoded pool IDs. All resources are discovered at runtime.

---

## Step 0 — Discover user pools (skip if user already named a pool)

```bash
aws cognito-idp list-user-pools --max-results 60 \
  --query 'UserPools[*].{Name:Name,Id:Id}' \
  --output table --no-cli-pager
```

Present the list and ask the user which pool to work with (or infer from context). If there is only one pool, proceed with it automatically. Store the pool ID as `$POOL_ID` for subsequent commands.

---

## Step 1 — Look up a user by email or username

```bash
aws cognito-idp admin-get-user \
  --user-pool-id "$POOL_ID" \
  --username "$EMAIL_OR_USERNAME" \
  --no-cli-pager
```

Display all attributes clearly. Key things to note:
- `UserStatus` — expected: `CONFIRMED`. Flag `UNCONFIRMED`, `FORCE_CHANGE_PASSWORD`, `DISABLED`, or `UNKNOWN`.
- `Enabled` — if `false`, the account is disabled.
- All `custom:` attributes — these often carry subscription status, plan tier, external IDs (e.g. Stripe customer ID), and role flags. Explain what each likely means.
- `UserCreateDate` and `UserLastModifiedDate` — note if the account is newly created or hasn't been modified in a long time.

---

## Step 2 — List users matching a filter

Use prefix filters for email or other standard attributes:

```bash
aws cognito-idp list-users \
  --user-pool-id "$POOL_ID" \
  --filter 'email ^= "user@example"' \
  --query 'Users[*].{Username:Username,Email:Attributes[?Name==`email`]|[0].Value,Status:UserStatus,Enabled:Enabled}' \
  --output table --no-cli-pager
```

Supported filter operators: `=`, `^=` (starts-with), `$=` (ends-with), `*=` (contains), `!=`.
Filterable attributes: `username`, `email`, `phone_number`, `name`, `given_name`, `family_name`, `preferred_username`, `cognito:user_status`, `status`, `sub`.

---

## Step 3 — Force-confirm an unconfirmed account

Use this when a user did not receive or click their confirmation email but should be activated anyway:

```bash
aws cognito-idp admin-confirm-sign-up \
  --user-pool-id "$POOL_ID" \
  --username "$USERNAME" \
  --no-cli-pager
```

After running, re-fetch the user (Step 1) and confirm `UserStatus` is now `CONFIRMED`.

---

## Step 4 — Reset a user's password

Sends a temporary password reset code to the user's registered email or phone:

```bash
aws cognito-idp admin-reset-user-password \
  --user-pool-id "$POOL_ID" \
  --username "$USERNAME" \
  --no-cli-pager
```

After running, the user will receive a reset code and their status will change to `RESET_REQUIRED`. Let the user know to check their inbox.

---

## Step 5 — Disable or enable a user

**Disable** (blocks all sign-in immediately):

```bash
aws cognito-idp admin-disable-user \
  --user-pool-id "$POOL_ID" \
  --username "$USERNAME" \
  --no-cli-pager
```

**Enable** (restores sign-in access):

```bash
aws cognito-idp admin-enable-user \
  --user-pool-id "$POOL_ID" \
  --username "$USERNAME" \
  --no-cli-pager
```

Disabling does not delete the user or their attributes. Existing sessions may remain valid until they expire — Cognito does not invalidate tokens on disable.

---

## Step 6 — Update a custom attribute

Use this to manually fix subscription status, plan tier, role flags, or any other custom attribute:

```bash
aws cognito-idp admin-update-user-attributes \
  --user-pool-id "$POOL_ID" \
  --username "$USERNAME" \
  --user-attributes Name="custom:subscription_status",Value="active" \
  --no-cli-pager
```

To update multiple attributes at once, repeat `Name=...,Value=...` entries:

```bash
aws cognito-idp admin-update-user-attributes \
  --user-pool-id "$POOL_ID" \
  --username "$USERNAME" \
  --user-attributes \
    Name="custom:subscription_status",Value="active" \
    Name="custom:plan",Value="pro" \
  --no-cli-pager
```

After updating, re-fetch the user (Step 1) to confirm the change took effect.

Note: You cannot update `email` or `phone_number` directly with this command if auto-verification is enabled. Use `admin-update-user-attributes` with `email_verified` set to `true` in the same call, or use the console.

---

## Step 7 — Delete a user

**This is irreversible. Always confirm before proceeding.**

Before deleting, show the user's full profile (Step 1) and explicitly list what will be lost:
- The Cognito account and all its attributes
- The ability to sign in with this username/email
- Any downstream records keyed on the Cognito `sub` (UUID) will become orphaned

Then ask for explicit confirmation. Only proceed after the user confirms.

```bash
aws cognito-idp admin-delete-user \
  --user-pool-id "$POOL_ID" \
  --username "$USERNAME" \
  --no-cli-pager
```

---

## Step 8 — Describe pool configuration

```bash
aws cognito-idp describe-user-pool \
  --user-pool-id "$POOL_ID" \
  --no-cli-pager \
  | jq '{
      Name: .UserPool.Name,
      MFA: .UserPool.MfaConfiguration,
      PasswordPolicy: .UserPool.Policies.PasswordPolicy,
      UsernameAttributes: .UserPool.UsernameAttributes,
      AutoVerifiedAttributes: .UserPool.AutoVerifiedAttributes,
      EstimatedNumberOfUsers: .UserPool.EstimatedNumberOfUsers,
      SchemaAttributes: [.UserPool.SchemaAttributes[]? | select(.Name | startswith("custom:"))]
    }'
```

This shows MFA settings, password policy, whether email/phone is used as the username, and all custom attributes defined in the schema.

---

## Step 9 — List app clients

```bash
aws cognito-idp list-user-pool-clients \
  --user-pool-id "$POOL_ID" \
  --query 'UserPoolClients[*].{Name:ClientName,Id:ClientId}' \
  --output table --no-cli-pager
```

To inspect a specific client's OAuth flows and callback URLs:

```bash
aws cognito-idp describe-user-pool-client \
  --user-pool-id "$POOL_ID" \
  --client-id "$CLIENT_ID" \
  --no-cli-pager \
  | jq '{
      ClientName: .UserPoolClient.ClientName,
      AllowedOAuthFlows: .UserPoolClient.AllowedOAuthFlows,
      CallbackURLs: .UserPoolClient.CallbackURLs,
      LogoutURLs: .UserPoolClient.LogoutURLs,
      ExplicitAuthFlows: .UserPoolClient.ExplicitAuthFlows
    }'
```
