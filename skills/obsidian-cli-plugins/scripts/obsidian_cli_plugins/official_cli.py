from typing import Any

from .constants import OFFICIAL_CLI_COMMANDS


def official_cli_index(category: str | None = None, query: str | None = None) -> dict[str, Any]:
    selected = OFFICIAL_CLI_COMMANDS
    if category:
        if category not in OFFICIAL_CLI_COMMANDS:
            raise SystemExit(f"Unknown official CLI category: {category}")
        selected = {category: OFFICIAL_CLI_COMMANDS[category]}
    rows = []
    needle = query.lower() if query else None
    for cat, commands in selected.items():
        for command, description in commands:
            if needle and needle not in command.lower() and needle not in description.lower():
                continue
            rows.append({"category": cat, "command": command, "description": description})
    return {
        "source": "Obsidian official CLI v1.12+ command index imported from obsidian-cli-official@4.0.2",
        "requires": ["Obsidian running", "Settings > General > Enable CLI", "obsidian binary in PATH or OBSIDIAN_BIN"],
        "syntax": {
            "vault": 'obsidian vault="Vault Name" <command>',
            "file": "file=Name for wikilink-style lookup, path=folder/file.md for exact paths",
            "parameters": 'name=value or name="value with spaces"',
        },
        "categories": sorted(OFFICIAL_CLI_COMMANDS),
        "total": len(rows),
        "commands": rows,
    }


def format_official_cli_index(data: dict[str, Any]) -> str:
    lines = [
        "# Obsidian Official CLI Commands",
        "",
        f"Source: {data['source']}",
        f"Total: {data['total']}",
        "",
        "Usage:",
        '- `obsidian vault="Vault Name" <command>`',
        '- Use `file=Name` for wikilink-style lookup or `path=folder/file.md` for exact paths.',
        '- Use `name=value` parameters and quote values with spaces.',
        "",
    ]
    current = None
    for row in data["commands"]:
        if row["category"] != current:
            current = row["category"]
            lines.extend([f"## {current}", ""])
        lines.append(f"- `{row['command']}` - {row['description']}")
    return "\n".join(lines)
