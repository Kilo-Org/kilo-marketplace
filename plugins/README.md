# Plugins Marketplace

Plugins extend Kilo with hooks, custom tools, auth providers, model providers, and runtime behavior. This directory lists community plugins that are published to npm.

When a user installs a plugin item, Kilo resolves the item `content` npm specifier and adds it to the `plugin` array in the config for each supported target. The item `id` must equal the npm package name, because the client uses it to detect installed plugins.

## Directory Structure

Each plugin is a directory named after its npm package. Scoped packages use a scope directory and a package subdirectory. Each package directory contains one `PLUGIN.yaml` file:

```
plugins/
  my-plugin/PLUGIN.yaml
  @scope/package/PLUGIN.yaml
```

## PLUGIN.yaml Fields

| Field | Required | Description |
|---|---|---|
| `id` | Yes | Valid npm package name. Must match the full path relative to `plugins/`, such as `@scope/package`. |
| `name` | Yes | Display name shown in the marketplace. |
| `description` | Yes | One or two sentences describing what the plugin does. |
| `category` | Yes | Primary category. See the list below. |
| `author` | Yes | Author or organization name. |
| `url` | Yes | Source repository or homepage URL. |
| `content` | Yes | Registry specifier for the same package as `id`, with an optional version, range, or tag. |

Valid categories: `business`, `data`, `development`, `observability`, `productivity`, `providers`, `search`, `web-automation`.

Do not set `tags`. The generator derives `tags` from `category`.

Supported `content` values include `my-plugin`, `my-plugin@1.2.3`, `my-plugin@^1.2.0`, `my-plugin@next`, and `@scope/package@~2.0.0`. npm aliases (`npm:`), local paths (`file:`), tarball URLs, and Git URLs are not supported. Package names must meet npm's rules for new packages, including lowercase names. The generated catalog retains the `{ items: [...] }` shape and full package name as `id`.

## Package Requirements

Publish the plugin to npm before submitting a catalog entry. Its published `package.json` must declare at least one supported target:

| Target | Manifest entry | Config |
|---|---|---|
| Server | `exports["./server"]`, or the legacy `main` entry | Kilo server config |
| TUI | `exports["./tui"]`, or `oc-themes` for theme packages | `tui.json` |

Export entries can be file path strings or objects with an `import` or `default` path. An `exports["."]` entry alone does not declare a supported target. For plugins that support both server and TUI, use separate `./server` and `./tui` entry modules. A modern server module default-exports an object with a `server` function; a TUI module default-exports an object with a `tui` function. Include the referenced files in the published npm package and test each declared target with Kilo. The generator validates catalog fields and npm specifiers, not the remote package manifest or runtime behavior.

Plugins execute code with the user's permissions. Review the source and dependencies before installation. Catalog validation is not a security review.

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

Install dependencies and run the generator from `bin/`, matching CI (Node.js 20.17 or newer and pnpm 9):

```bash
cd bin
pnpm install
pnpm exec tsx generate-plugins-marketplace.ts
pnpm test
pnpm run typecheck:plugins
```

## Contribution Workflow

1. Check for an existing entry with the same npm package name.
2. Publish and test the package with the supported manifest entries described above.
3. Add `plugins/<package>/PLUGIN.yaml` or `plugins/@scope/<package>/PLUGIN.yaml`. Set `id` to the exact package name, not a display name or versioned specifier.
4. Run the generator, tests, and typecheck commands above. Review the generated `plugins/marketplace.yaml` diff.
5. Submit a pull request with the manifest and generated catalog. Describe what the plugin does, its source and npm package, and which targets you tested.
