# EasyGerber: AI PCB design, layout, and routing

This entry connects Kilo to EasyGerber's hosted board-design tools. Layout, routing, and scoring run on EasyGerber's servers.

## Setup

Install **EasyGerber** from the MCP marketplace and select **Remote**. No local server, Node.js package, API key, or EasyGerber account is needed for a new guest connection. Keep normal tool approvals enabled.

For manual setup in current Kilo clients, merge this entry into the `mcp` object in your Kilo configuration, preserving existing entries:

```json
{
  "mcp": {
    "easygerber": {
      "type": "remote",
      "url": "https://www.easygerber.com/api/mcp"
    }
  }
}
```

Use Settings → MCP in the VS Code extension, or the global `~/.config/kilo/kilo.jsonc` or project `.kilo/kilo.jsonc` file. See [Kilo's MCP guide](https://kilo.ai/docs/automate/mcp/using-in-kilo-code) for the current client controls. The marketplace's `streamable-http` configuration is converted to the client's `remote` format during installation.

Confirm the connection exposes EasyGerber tools, including `search_parts`, `get_part`, and `start_guest_session`. Tools and schemas are discovered from the live service; no companion skill is required.

## First board

Ask Kilo:

> Use EasyGerber to make a passive signal-and-ground pass-through board with two published two-pin connectors. Confirm their catalog pins, use the app's supported defaults, generate the layout, show the preview, check for blocking issues, and export the manufacturing ZIP and editable EasyGerber file. Do not place an order.

For a new board, the agent starts a guest session directly with `start_guest_session`, or reuses the task's existing session or authorized account. It searches and inspects catalog parts before creating the schematic, lets the service hydrate hidden routing constraints, and follows the live tool schemas for creation, generation, previews, checks, and exports. Generation is asynchronous; wait for the returned operation before inspecting its result. Successful generation is not an electrical or manufacturing safety certification.

A guest session supports one board. Keep its guest token and private viewer link private; anyone with the link can access the guest design. Do not put them in project files, logs, issues, or public recordings. Download links expire after fifteen minutes, independently of the guest board's lifetime.

## Account boards

Guest access does not limit the service to guest boards. Saved account boards and organization work require normal EasyGerber sign-in and OAuth consent. The default guest-capable URL connects without sign-in; in Kilo CLI 7.8.15, asking it to start authentication on that URL did not open an OAuth redirect.

For account setup in Kilo, use `https://www.easygerber.com/api/mcp/account` instead. That entry requires sign-in before discovery and does not start in guest mode. Complete Kilo's native authorization flow, without copying access tokens into configuration or chat. These endpoints have distinct OAuth resources: when switching, remove the old connection through the client's controls, create a new one, and authorize it afresh. Do not transfer existing tokens or retain duplicate active connections. Account permissions and normal plan limits still apply.

To save an existing guest board to your account, retain its original guest token and resume `claim_guest_board` after authorization. Signing in alone does not prove the board has been claimed; verify the returned account board. Never create a replacement guest session to bypass limits or recover a lost capability.

## Source and data

The [public integration repository](https://github.com/EasyGerber/easygerber-agent-plugin) contains connection metadata and workflow instructions. It does not contain the proprietary board engines. Board requirements and authorized tool requests go to EasyGerber's hosted service; your selected model provider handles Kilo prompts. Send only information needed for the requested design.

Creating or exporting a board does not authorize deletion, purchasing fabrication, or public sharing. For detailed tool workflows and privacy information, see the [public README](https://github.com/EasyGerber/easygerber-agent-plugin#readme) and [workflow reference](https://github.com/EasyGerber/easygerber-agent-plugin/blob/main/skills/easygerber/references/workflow.md).

## Validation

The guest workflow was checked with Kilo CLI 7.8.15 using its experimental headless MCP Apps tool route: connection and tool discovery, catalog part selection, creation of one board with two published connectors, server-side generation, a saved-layout check with no blocking issues, and a preview. The returned 3D board viewer was also inspected in a browser. This exercised Kilo's native MCP transport, without interactive model chat or the GUI approval flow. Export operations were not part of this Kilo check. The account-only connection reached EasyGerber's normal OAuth consent screen; account authorization and account operations have not yet been completed in this validation. These checks do not establish compatibility with every Kilo client version.
