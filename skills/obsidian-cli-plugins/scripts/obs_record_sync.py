#!/usr/bin/env python3
"""Cross-platform launcher for the Obsidian record-sync workflow."""
from __future__ import annotations

import sys

from obsidian_cli_plugins.cli import main


GLOBAL_OPTIONS_WITH_VALUE = {"--vault", "--vault-path"}


def split_global_args(argv: list[str]) -> tuple[list[str], list[str]]:
    """Keep top-level workflow options before the record-sync subcommand."""
    global_args: list[str] = []
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--":
            return global_args, argv[index + 1 :]
        if any(arg.startswith(option + "=") for option in GLOBAL_OPTIONS_WITH_VALUE):
            global_args.append(arg)
            index += 1
            continue
        if arg in GLOBAL_OPTIONS_WITH_VALUE:
            global_args.append(arg)
            if index + 1 < len(argv):
                global_args.append(argv[index + 1])
                index += 2
                continue
            return global_args, []
        break
    return global_args, argv[index:]


def record_sync_argv(argv: list[str]) -> list[str]:
    global_args, record_args = split_global_args(argv)
    if record_args[:1] == ["record-sync"]:
        record_args = record_args[1:]
    return [sys.argv[0], *global_args, "record-sync", *record_args]


if __name__ == "__main__":
    sys.argv = record_sync_argv(sys.argv[1:])
    main()
