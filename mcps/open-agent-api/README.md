# Open Agent API for Kilo

This local stdio entry connects to a separately run
[Open Agent API](https://github.com/jiangxingfan1-coder/Open-Agent-API) gateway.
It doesn't install a gateway or switch Kilo's model provider.

1. Install the CLI using the
   [setup guide](https://jiangxingfan1-coder.github.io/Open-Agent-API/docs/install.html#source)
   and make sure `oaa` is on Kilo's PATH. This entry was tested with
   [v0.0.64](https://github.com/jiangxingfan1-coder/Open-Agent-API/releases/tag/v0.0.64)
   and requires the `oaa mcp` subcommand. Use `oaa quickstart` for a local
   offline sample that requires no provider key.
2. Choose a dedicated gateway key with `read` scope and only the agents you
   want to inspect. Store its value in a private file. Choose **Enter key-file
   path** and supply the absolute file path, not the key itself. For
   **Use process environment**, set `OAA_TOKEN_FILE` to that path before
   launching Kilo. With either method, set `OAA_GATEWAY_URL` in Kilo's
   process environment if the gateway isn't at `http://127.0.0.1:8787`.
3. With the MCP configured, confirm `kilo mcp list` reports it as connected.
   Use `oaa_list_agents` to inspect what's available.

The gateway enforces the key's scope. The tool catalog can show invocation
tools, but a reader key cannot invoke an agent. Do not configure an admin
token or hardcode a token in a project file. See the
[MCP operations guide](https://github.com/jiangxingfan1-coder/Open-Agent-API/blob/main/docs/cli.md#mcp-and-integrations)
for the rest of the tool surface.

Verified with Kilo CLI 7.8.32 on macOS arm64 using both generated
configurations: a reader key file connected, and a missing file failed without
starting an agent run. The parameterized install stores only the local file
path in Kilo's configuration. Use global configuration or keep any
project-local config containing a machine-specific path out of version
control. The Marketplace UI and hosted Kilo clients were not tested.
