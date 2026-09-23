# Plugins Marketplace

Plugins extend Kilo with hooks, custom tools, auth providers, model providers, and runtime behavior. This directory lists community plugins that are published to npm or hosted in a public git repository.

When a user installs a plugin item, Kilo resolves the item `content` specifier and adds it to the `plugin` array in the config for each supported target. The `content` value is either an npm registry specifier or a git source specifier. The item `id` must equal the npm package name for registry entries, or the normalized git identity for git entries, because the client uses it to detect installed plugins.

## Directory Structure

Each plugin is a directory named after its `id`. npm packages use the package name, with a scope directory and a package subdirectory for scoped packages. Git sources use the normalized git identity as a nested path. Each plugin directory contains one `PLUGIN.yaml` file:

```
plugins/
  my-plugin/PLUGIN.yaml
  @scope/package/PLUGIN.yaml
  github.com/owner/repo/PLUGIN.yaml
  github.com/owner/repo/plugins/x/PLUGIN.yaml
```

## PLUGIN.yaml Fields

| Field | Required | Description |
|---|---|---|
| `id` | Yes | For registry entries, a valid npm package name that matches the full path relative to `plugins/`, such as `@scope/package`. For git entries, the normalized git identity. |
| `name` | Yes | Display name shown in the marketplace. |
| `description` | Yes | One or two sentences describing what the plugin does. |
| `category` | Yes | Primary category. See the list below. |
| `author` | Yes | Author or organization name. |
| `url` | Yes | Source repository or homepage URL. |
| `content` | Yes | npm registry specifier for the same package as `id`, or a git source specifier. |

Valid categories: `business`, `data`, `development`, `observability`, `productivity`, `providers`, `search`, `web-automation`.

Do not set `tags`. The generator derives `tags` from `category`.

### Registry Content

Supported registry `content` values include `my-plugin`, `my-plugin@1.2.3`, `my-plugin@^1.2.0`, `my-plugin@next`, and `@scope/package@~2.0.0`. For registry entries, the `id` must equal the package name. npm aliases (`npm:`), local paths (`file:`), tarball URLs, and bare Git URLs are not supported; use a git source instead. Package names must meet npm's rules for new packages, including lowercase names. The generated catalog retains the `{ items: [...] }` shape and full package name as `id`.

### Git Content

A plugin can be hosted in a public git repository instead of npm. Set `content` to a git spec:

```
git:<repo>[@ref][#subpath]
```

| Part | Required | Description |
|---|---|---|
| `repo` | Yes | `github.com/owner/repo`, or a full URL with an `https`, `http`, `git`, or `ssh` scheme. The repo must not contain `@`, so SSH URLs with a `user@` prefix and scp-style `git@host:path` are not supported. Local paths and `file:` URLs are not allowed in the catalog; use them only in your own config. |
| `ref` | No | Branch, tag, or commit after the last `@`. |
| `subpath` | No | Plugin directory inside the repository, after the first `#`. |

For git entries, `id` must equal the normalized git identity: `git/` plus the repo without its scheme and without a trailing `.git`, plus the subpath appended as `/subpath` when present. For example `git:github.com/owner/repo@v1` has id `git/github.com/owner/repo`, and `git:github.com/owner/repo#plugins/x` has id `git/github.com/owner/repo/plugins/x`. Malformed git specs are rejected, including refs that start with `-` or contain `..`. Because `id` is also the directory path under `plugins/`, that first example lives in `plugins/git/github.com/owner/repo/`.

Git plugins must be self-contained. Kilo clones the repository at the given ref and loads the plugin directly; it does not install npm dependencies for git plugins in this version. Vendor any runtime dependencies into the repository.

You can host the plugin in any public git repository, or inside this marketplace repository. To host it inside the marketplace repository, commit the plugin source in the same pull request and point `content` at this repository with a subpath. The entry is still added with a pull request; direct pushes are not accepted.

## Package Requirements

For registry entries, publish the plugin to npm before submitting a catalog entry. For git entries, the repository must contain a `package.json`. The `package.json` must declare at least one supported target:

| Target | Manifest entry | Config |
|---|---|---|
| Server | `exports["./server"]`, or the legacy `main` entry | Kilo server config |
| TUI | `exports["./tui"]`, or `oc-themes` for theme packages | `tui.json` |

Export entries can be file path strings or objects with an `import` or `default` path. An `exports["."]` entry alone does not declare a supported target. For plugins that support both server and TUI, use separate `./server` and `./tui` entry modules. A modern server module default-exports an object with a `server` function; a TUI module default-exports an object with a `tui` function. Include the referenced files in the published npm package or git repository and test each declared target with Kilo. For git entries, keep the plugin self-contained; Kilo does not install its dependencies. The generator validates catalog fields and content specifiers, not the remote package manifest or runtime behavior.

Plugins execute code with the user's permissions. Review the source and dependencies before installation. Catalog validation is not a security review.

## Examples

Registry plugin:

```yaml
id: my-plugin
name: My Plugin
description: Adds custom tools and provider hooks to Kilo.
category: providers
author: your-name
url: https://github.com/your-name/my-plugin
content: my-plugin
```

Git plugin:

```yaml
id: github.com/your-name/my-plugin
name: My Plugin
description: Adds custom tools and provider hooks to Kilo.
category: providers
author: your-name
url: https://github.com/your-name/my-plugin
content: git:github.com/your-name/my-plugin@v1
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

1. Choose the source. For a registry plugin, publish and test the package with the supported manifest entries described above, then check for an existing entry with the same npm package name. For a git plugin, host the self-contained plugin in a public git repository or inside this repository.
2. Add the `PLUGIN.yaml` entry under `plugins/<id>/PLUGIN.yaml`. The directory path must equal `id`. For a registry plugin, set `id` to the exact package name, not a display name or versioned specifier. For a git plugin, set `id` to the normalized git identity described above.
3. Run the generator, tests, and typecheck commands above. Review the generated `plugins/marketplace.yaml` diff.
4. Submit a pull request with the manifest and generated catalog. Describe what the plugin does, its source, and which targets you tested. The pull request is the only supported path; direct pushes are not accepted.
