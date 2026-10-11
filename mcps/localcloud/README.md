# LocalCloud

Give your coding agent a cloud environment it can actually work with. LocalCloud runs a local Google Cloud development environment in Docker and connects it to the agent through the installed CLI over stdio. Discover services, obtain standard SDK connection settings, inspect resources, query test data, and diagnose failures through MCP. Run local workflows with zero Google Cloud service charges and create projects for experiments within your machine’s capacity.

## Requirements and setup

Use macOS or Linux with a working Docker engine, the LocalCloud CLI, and its Docker image. Install the current CLI through Homebrew:

```sh
brew install LocalGCloud/tap/localcloud
command -v localcloud
lc start --local-only
```

For Linux/native archives, follow the [official MCP setup guide](https://github.com/LocalGCloud/localcloud-cli/blob/main/docs/mcp.md). The first start can download the image. Start the runtime before connecting so a client’s startup timeout does not interrupt that download. Local workflows need no real Google Cloud project, billing credentials, or API key. The CLI and runtime use the [LocalCloud Public Preview License](https://local.cloud/license/).

## Kilo installation

The marketplace entry uses the **Native LocalCloud CLI (stdio)** option. Enter the absolute path printed by `command -v localcloud` into **LocalCloud executable path**. This is a local executable; the documentation URL is an HTML guide and must not be entered as a remote MCP endpoint.

For manual Kilo CLI setup, create `kilo.json` in your project with the following configuration, replacing the example path:

```json
{
  "mcp": {
    "localcloud": {
      "type": "local",
      "command": ["/absolute/path/to/localcloud", "mcp"],
      "enabled": true,
      "timeout": 120000
    }
  },
  "permission": {
    "localcloud_*": "ask"
  }
}
```

Then run `kilo mcp list` and check that LocalCloud is connected. Current Kilo CLI and VS Code extension versions share the `mcp` object with `type: "local"` and a command array; the extension also supports `kilo.jsonc`. Follow the [official Kilo MCP guide](https://kilo.ai/docs/automate/mcp/using-in-kilo-code) for the settings editor and configuration location.

Keep tool approval enabled and review calls that change resources. MCP management writes and destructive actions are disabled by default; an agent executing application code with an SDK can still write test resources.

## First workflow

Ask your agent:

> Use LocalCloud to build and test a Cloud Storage upload-and-read workflow with the standard Python SDK. First discover the service and SDK settings through MCP. Use local endpoints, create uniquely named test resources, assert the returned content, and clean up only resources created by this test. Stop and explain if an operation is unsupported.

Other examples include verifying Pub/Sub publish/pull/acknowledge behavior, asserting a BigQuery query result, and investigating failed integration tests with diagnostics. MCP supplies context and inspection; the coding client’s ordinary execution tools run the application code.

The complete tool/resource/prompt reference is in the [official MCP guide](https://github.com/LocalGCloud/localcloud-cli/blob/main/docs/mcp.md); the initialized catalog is authoritative. Compatibility varies by service and operation. Verify production behavior against Google Cloud before deployment. See the [privacy disclosure](https://github.com/LocalGCloud/localcloud-cli/blob/main/docs/mcp-privacy.md) for telemetry, local data, and what reaches the agent client.

## Qualification

On 2026-10-11, Kilo CLI 7.8.8 on macOS arm64 connected to the published native LocalCloud CLI 0.1.11 over stdio against the published LocalCloud runtime 0.1.5. Marketplace generation and its 119 tests passed, as did the MCP generator typecheck. This is a direct local connection test; installation from the curated catalog can be verified after the listing is merged and deployed. No Kilo extension or model-driven workflow qualification is claimed by the connection check.

[Website](https://local.cloud/) · [Support](https://github.com/LocalGCloud/localcloud-cli/issues)
