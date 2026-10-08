import os
import pathlib
import re


DEFAULT_VAULT = os.environ.get("OBSIDIAN_VAULT", "obsidian-2026")
DEFAULT_VAULT_PATH = pathlib.Path(os.environ.get("OBSIDIAN_VAULT_PATH", "~/git/obsidian-2026")).expanduser()
PRIVATE_OUTPUT_DIR = pathlib.Path(os.environ.get("OBSIDIAN_WORKFLOW_OUTPUT_DIR", "~/.cache/obsidian-cli-plugins")).expanduser()

PLAN_DIRS = {
    "day": "20_plan/21_daily",
    "week": "20_plan/22_weekly",
    "month": "20_plan/23_monthly",
    "quarter": "20_plan/24_quarterly",
    "year": "20_plan/25_annual",
}

DANGEROUS_COMMAND_RE = re.compile(
    r"(delete|remove|uninstall|reset|discard|clear|cleanup|purge|wipe|trash|unlink|disable|restrict|restore|publish:remove|install|enable)",
    re.IGNORECASE,
)
SENSITIVE_COMMAND_RE = re.compile(
    r"(^|:)(dev|eval|cdp|console|debug|dom|screenshot|mobile|history|sync|publish)(:|$)",
    re.IGNORECASE,
)
SECRET_REDACTIONS = [
    re.compile(r"(?i)(password|passwd|secret|token|api[-_]?key|credential|cookie|session|bearer)(\s*[=:]\s*)[^\s]+"),
    re.compile(r"(?i)(https?://)([^/\s:@]+:)?[^@\s/]+@"),
    re.compile(r"(?i)(ghp|github_pat|glpat|sk|xox[baprs])-[-A-Za-z0-9_]{12,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL),
]
JOURNALS_COMMANDS = {
    "day": {
        -1: "journals::open-yesterday's-note",
        0: "journals::open-today's-note",
        1: "journals::open-tomorrow's-note",
    },
    "week": {
        -1: "journals::open-last-week-note",
        0: "journals::open-weekly-note",
        1: "journals::open-next-week-note",
    },
    "month": {
        -1: "journals::open-last-month-note",
        0: "journals::open-monthly-note",
        1: "journals::open-next-month-note",
    },
    "quarter": {
        -1: "journals::open-last-quarter-note",
        0: "journals::open-quarterly-note",
        1: "journals::open-next-quarter-note",
    },
    "year": {
        -1: "journals::open-last-year-note",
        0: "journals::open-yearly-note",
        1: "journals::open-next-year-note",
    },
}
OFFICIAL_CLI_COMMANDS = {
    "general": [
        ("help", "Show help or help for a specific command"),
        ("version", "Show Obsidian version"),
        ("reload", "Reload the app window"),
        ("restart", "Restart the app"),
    ],
    "daily": [
        ("daily", "Open daily note"),
        ("daily:path", "Get daily note path"),
        ("daily:read", "Read daily note contents"),
        ("daily:append", "Append content to daily note"),
        ("daily:prepend", "Prepend content to daily note"),
    ],
    "files": [
        ("file", "Show file info"),
        ("files", "List files in vault"),
        ("folder", "Show folder info"),
        ("folders", "List folders in vault"),
        ("open", "Open a file"),
        ("create", "Create a new file"),
        ("read", "Read file contents"),
        ("append", "Append content to a file"),
        ("prepend", "Prepend content to a file"),
        ("move", "Move or rename a file"),
        ("rename", "Rename a file"),
        ("delete", "Delete a file"),
    ],
    "search": [
        ("search", "Search vault for text"),
        ("search:context", "Search with matching line context"),
        ("search:open", "Open search view"),
    ],
    "tasks": [
        ("tasks", "List tasks in the vault"),
        ("task", "Show or update a task"),
    ],
    "tags": [
        ("tags", "List tags in the vault"),
        ("tag", "Get tag info"),
    ],
    "properties": [
        ("properties", "List properties in the vault"),
        ("property:set", "Set a property on a file"),
        ("property:remove", "Remove a property from a file"),
        ("property:read", "Read a property value"),
    ],
    "aliases": [("aliases", "List aliases in the vault")],
    "links": [
        ("backlinks", "List backlinks to a file"),
        ("links", "List outgoing links from a file"),
        ("unresolved", "List unresolved links"),
        ("orphans", "Files with no incoming links"),
        ("deadends", "Files with no outgoing links"),
    ],
    "outline": [("outline", "Show headings for a file")],
    "bookmarks": [
        ("bookmarks", "List bookmarks"),
        ("bookmark", "Add a bookmark"),
    ],
    "bases": [
        ("bases", "List all base files"),
        ("base:views", "List views in a base"),
        ("base:create", "Create a new item in a base"),
        ("base:query", "Query a base and return results"),
    ],
    "templates": [
        ("templates", "List templates"),
        ("template:read", "Read template content"),
        ("template:insert", "Insert template into active file"),
    ],
    "commands-hotkeys": [
        ("commands", "List available command IDs"),
        ("command", "Execute an Obsidian command"),
        ("hotkeys", "List hotkeys"),
        ("hotkey", "Get hotkey for a command"),
    ],
    "tabs-workspaces": [
        ("tabs", "List open tabs"),
        ("tab:open", "Open a new tab"),
        ("workspace", "Show workspace tree"),
        ("workspaces", "List saved workspaces"),
        ("workspace:load", "Load a saved workspace"),
        ("workspace:save", "Save current layout"),
        ("workspace:delete", "Delete a saved workspace"),
    ],
    "history-diff": [
        ("diff", "List or diff local/sync versions"),
        ("history", "List file history versions"),
        ("history:list", "List files with history"),
        ("history:read", "Read a file history version"),
        ("history:restore", "Restore a file history version"),
        ("history:open", "Open file recovery"),
    ],
    "sync": [
        ("sync", "Pause or resume sync"),
        ("sync:status", "Show sync status"),
        ("sync:history", "List sync version history"),
        ("sync:read", "Read a sync version"),
        ("sync:restore", "Restore a sync version"),
        ("sync:open", "Open sync history"),
        ("sync:deleted", "List deleted files in sync"),
    ],
    "publish": [
        ("publish:site", "Show publish site info"),
        ("publish:list", "List published files"),
        ("publish:status", "Show publish status"),
        ("publish:add", "Publish files"),
        ("publish:remove", "Unpublish files"),
        ("publish:open", "Open published site"),
    ],
    "themes-snippets": [
        ("themes", "List installed themes"),
        ("theme", "Show active theme or get info"),
        ("theme:set", "Set active theme"),
        ("theme:install", "Install a community theme"),
        ("theme:uninstall", "Uninstall a theme"),
        ("snippets", "List installed CSS snippets"),
        ("snippets:enabled", "List enabled CSS snippets"),
        ("snippet:enable", "Enable a CSS snippet"),
        ("snippet:disable", "Disable a CSS snippet"),
    ],
    "plugins": [
        ("plugins", "List installed plugins"),
        ("plugins:enabled", "List enabled plugins"),
        ("plugins:restrict", "Toggle restricted mode"),
        ("plugin", "Get plugin info"),
        ("plugin:enable", "Enable a plugin"),
        ("plugin:disable", "Disable a plugin"),
        ("plugin:install", "Install a community plugin"),
        ("plugin:uninstall", "Uninstall a community plugin"),
        ("plugin:reload", "Reload a plugin"),
    ],
    "vault": [
        ("vault", "Show vault info"),
        ("vaults", "List known vaults"),
        ("vault:open", "Open a vault"),
    ],
    "random": [
        ("random", "Open a random note"),
        ("random:read", "Read a random note"),
    ],
    "unique": [("unique", "Create unique note")],
    "web": [("web", "Open URL in web viewer")],
    "wordcount": [("wordcount", "Count words and characters")],
    "recents": [("recents", "List recently opened files")],
    "developer": [
        ("devtools", "Toggle Electron dev tools"),
        ("eval", "Execute JavaScript"),
        ("dev:screenshot", "Take a screenshot"),
        ("dev:console", "Show captured console messages"),
        ("dev:errors", "Show captured errors"),
        ("dev:css", "Inspect CSS with source locations"),
        ("dev:dom", "Query DOM elements"),
        ("dev:cdp", "Run Chrome DevTools Protocol command"),
        ("dev:debug", "Attach or detach CDP debugger"),
        ("dev:mobile", "Toggle mobile emulation"),
    ],
}
