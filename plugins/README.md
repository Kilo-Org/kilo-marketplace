# Plugins Marketplace

Plugins extend Kilo with hooks, custom tools, auth providers, model providers, and runtime behavior. This directory lists community plugins that are published to npm.

When a user installs a plugin item, Kilo adds the item `content` npm specifier to the `plugin` array in the Kilo config and resolves the package from npm. The item `id` must equal the npm package name, because the client uses it to detect installed plugins.

## Directory Structure

Each plugin is a directory named after its npm package. The directory contains one `PLUGIN.yaml` file:

```
plugins/
└── my-plugin/
    └── PLUGIN.yaml
```

## PLUGIN.yaml Fields

| Field | Required | Description |
|---|---|---|
| `id` | Yes | npm package name. Must match the directory name. |
| `name` | Yes | Display name shown in the marketplace. |
| `description` | Yes | One or two sentences describing what the plugin does. |
| `category` | Yes | Primary category. See the list below. |
| `author` | Yes | Author or organization name. |
| `url` | Yes | Source repository or homepage URL. |
| `content` | Yes | npm specifier to install, for example `my-plugin` or `my-plugin@1.2.3`. |

Valid categories: `business`, `data`, `development`, `observability`, `productivity`, `providers`, `search`, `web-automation`.

Do not set `tags`. The generator derives `tags` from `category`.

## Example

```yaml
id: my-plugin
name: My Plugin
description: Adds custom tools and provider hooks to Kilo.
category: providers
author: your-name
url: https://github.com/your-name/my-plugin
content: my-plugin
```

## Regenerating marketplace.yaml

The committed `plugins/marketplace.yaml` is generated from the per-plugin `PLUGIN.yaml` files. Do not edit it manually.

From the repository root:

```bash
npx tsx bin/generate-plugins-marketplace.ts
```

From the `bin/` directory, matching the CI workflow:

```bash
pnpm exec tsx generate-plugins-marketplace.ts
```
