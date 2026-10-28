"""Thin CLI entry point so ``python -m query_tableau_data_py`` works.

This is a minimal wrapper — not a full CLI app.  For agent workflows,
import ``main.py`` directly and call ``run()`` or use ``Session``.

``.env`` loading is handled by ``pydantic-settings`` via ``SdkConfig``,
which searches for ``.env`` in the current working directory first, then
in the skill root directory (next to ``pyproject.toml``).
"""

from query_tableau_data_py.main import main

if __name__ == "__main__":
    main()
