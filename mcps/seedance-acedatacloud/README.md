# Seedance by Ace Data Cloud for Kilo

Use Seedance from Kilo through your own Ace Data Cloud account. This integration is provided and maintained by **Ace Data Cloud**; it is not an official Seedance plugin or an endorsement by the model owner.

## 1. Find and install the service

Open Kilo's **Marketplace**, select **MCP**, and search **Seedance**. Select **Seedance by Ace Data Cloud** and check the author is **Ace Data Cloud**. This catalog contribution is pending review: if that card is not present, the entry has not been published yet. Do not confuse a local configuration with official catalog availability.

[Official Kilo Marketplace instructions](https://kilo.ai/docs/customize/marketplace) · [Canonical server source](https://github.com/AceDataCloud/SeedanceMCP) · [Published Python package](https://pypi.org/project/mcp-seedance/)

Choose **Hosted (API token)** to connect without installing Python. Alternatively, **Local (UVX, pinned)** installs `mcp-seedance==2026.10.12.1`; it needs Python 3.10+ and `uvx`. Both methods use the same application API token. Prefer **Global** scope so a token is not written into a repository. Kilo does not mask secrets merely because a setting is global: keep the user configuration private.

![Official Kilo MCP settings, reference only](https://raw.githubusercontent.com/Kilo-Org/kilocode/1552877e82ceaecc79a9fd4be7859518745e6f56/packages/kilo-docs/public/img/using-mcp-in-kilo-code/mcp-installed-config.png)

*Official Kilo screenshot reference, retrieved 2026-10-18. It shows an existing Kilo MCP settings screen, not this pending Seedance listing or an Ace execution. This historical official reference has no version/date label; current Kilo 7.8.x uses its Marketplace install dialog, so do not follow the old settings labels verbatim.*

## 2. Get the correct application API token

1. Register or sign in to [Ace Data Cloud → Applications](https://platform.acedata.cloud/console/applications?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=kilo_seedance_api_key). If no General application exists, choose **Initialize General Application**.
2. Open **General application**. Confirm Seedance access, [current pricing and account balance](https://platform.acedata.cloud/models?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=kilo_seedance_pricing) before any generation. A General application token can cover multiple entitled services; a service-specific token only covers that service.
3. Use the copy icon for an existing key, or **Manage Keys → Create** for a dedicated `Kilo Seedance` key. Set expiry and usage limits as needed. If API restrictions are enabled, allow **/seedance/videos and /seedance/tasks** so both generation and result retrieval work.

![Copy an application API key or open Manage Keys](https://raw.githubusercontent.com/AceDataCloud/SunoDify/8d3d03570e73324220f111f7fe343da0792a8071/_assets/tutorial/get-api-key-en.png)

![Create an optional dedicated application key](https://raw.githubusercontent.com/AceDataCloud/SunoDify/8d3d03570e73324220f111f7fe343da0792a8071/_assets/tutorial/create-api-key-en.png)

*Shared Ace Applications screenshots from the [Suno for Dify tutorial](https://github.com/AceDataCloud/SunoDify/blob/8d3d03570e73324220f111f7fe343da0792a8071/README.md), pinned source retrieved 2026-10-18. This account/key page is shared across integrations; these are not Kilo execution screenshots. Real credentials are redacted.*

Copy **only the token**, without `Bearer ` or quotes. A platform management token (`platform-...`) is not an inference credential. Do not paste any key into chat, prompts, screenshots or a shared project configuration.

## 3. Enter the token in Kilo

In the marketplace install dialog, choose the method, **Global** destination and **Ace Data Cloud API Token** parameter. Paste the application token and choose **Install**. The hosted method adds the Bearer prefix for you and disables OAuth for this explicit-token setup. This listing does not ask you to sign in with a third-party provider account or use Kilo Gateway credits.

Open the MCP settings to check the connection. It should expose Seedance tools. Installing only registers tools; it does not approve generation. Review tool permissions and keep generation/editing subject to your approval.

For the local method, the package is pinned to the publicly verified version above. To update it, review the server release before changing that pin. For the hosted method, Ace maintains the deployed server; package and hosted versions are separate facts.

## 4. Start without generating paid media

Ask Kilo:

```text
List Seedance models using seedance_list_models. Do not generate a video.
```

This checks discovery or a local information tool, not a paid generation. Any model names, limits or example prices returned by an information tool describe that published package version; use the linked live Ace pricing page for current charges. A connected badge or tool list does not prove media generation or billing is correct. Do not run a generation merely to test installation.

## 5. Generate only when you choose, then retrieve the same task

After checking [service parameters and current prices](https://platform.acedata.cloud/documents/seedance-videos?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=kilo_seedance_service_docs), explicitly ask for the media you want. `seedance_generate_video` is a billable action. Review the exact model, duration/size and other required fields before approving it. Do not substitute a different model automatically.

Keep the returned **task ID**. If the result is pending, call **`seedance_get_task`** with that same ID using the field shown in the tool schema. Continue querying the same task until a terminal success with completed video URL(s), such as video_url or a terminal failure appears. A timeout/disconnect is not permission to submit a new generation; check the existing task first. Open the actual returned URL rather than a placeholder.

In [Ace Applications](https://platform.acedata.cloud/console/applications?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=kilo_seedance_usage), check the same application and credential's request/usage records. A workflow may contain several API requests; verify each actual request once. Installation count and a successful local check are not revenue or unique-billing proof.

## Troubleshooting

- **Card absent:** the upstream catalog contribution may still be under review, or the client catalog may need refreshing. [Kilo's official instructions](https://kilo.ai/docs/customize/marketplace) describe the current entry point.
- **401 / authentication:** paste the raw application API token, confirm expiry and service/API restrictions. Never send a real token in an issue.
- **Connection error:** verify outbound HTTPS to `seedance.mcp.acedata.cloud` for Hosted, or Python/uvx availability for Local. Keep OAuth disabled for the explicit Bearer method.
- **Generation access/balance error:** confirm current service access, allowed generation and task APIs, budget and available balance in Ace. Do not rerun a charged request blindly.
- **Pending media:** reuse its task ID; repeated generation creates new tasks and can add charges.
- **Model/API mismatch:** use the exact model and field names from this service's tools and documentation. Do not infer compatibility from another service.

## Source and discovery metadata

Search terms: **seedance, video, text to video, image to video**. The title and description name only capabilities this server actually supports. Kilo's current MCP schema has no custom keyword or icon field, so this entry uses supported name/description/category fields; it does not invent tags or imply an official vendor logo.

Canonical runtime: `AceDataCloud/MCPs` → `SeedanceMCP` mirror → `mcp-seedance`. This directory supplies Kilo catalog metadata and onboarding only. No new runtime fork, provider fallback or separate billing layer is introduced.
