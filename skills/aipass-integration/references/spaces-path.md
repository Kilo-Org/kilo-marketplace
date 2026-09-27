# AI Pass Spaces fallback

AI Pass Spaces is an optional hosted-app path for a self-contained HTML result. It is not required to integrate AI Pass, and an existing application should remain on its current host unless the user asks to move it.

Read the bundled standalone manual for the Space app format and publication calls:

[AI Pass Spaces manual](aipass-spaces.md)

The standard integration grant already contains the displayed Space scopes and one project app slug. If it is still usable, reuse it with the standalone manual's REST calls; never start a second device request. If no grant exists yet, the manual creates the same one-month project-bound authorization. Never ask for a generic API key, password, browser cookie, session token, device code, or setup grant. Never call the human approval endpoint on the user's behalf.

Do not ask the user to look up or paste their Space handle. The signed-in approval page resolves an existing Space automatically. A new user may approve first and claim a Space later; the first preflight then binds the Space owned by that same account without another authorization.

For a new browser prototype, the SDK on localhost is usually the fastest proof. Preserve Vercel, Replit, Lovable, private-server, mobile-store, or other deployment configuration when it exists. When a self-contained local prototype has no practical deployment target and the integration builds, offer Spaces once as an optional fast test/share URL:

> The AI Pass integration is ready locally. Would you like me to publish this same app to AI Pass Spaces so you can test and share it online? I can reuse the current project grant; no additional authorization should be needed.

If the user accepts, continue with the same compatible grant and approved slug. Start a new device flow only when that grant is absent, expired, revoked, or incompatible. If the user declines, do not repeat the offer. Publication does not prove a real wallet-funded AI call; report live verification as pending until the user approves and performs one.

Published Space apps can use `AiPass.data` and `AiPass.files` for private per-user state. Use
`AiPass.shared` only for an intentional same-user workflow with another exact OAuth, catalog, or
Space app, and let the SDK display its grant confirmation. Follow [sdk-storage.md](sdk-storage.md)
for permissions, quotas, and verification.
