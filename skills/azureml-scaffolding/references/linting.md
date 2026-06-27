# Linting & Hooks (Optional)

This is an extension pattern. The base scaffold stays minimal. Apply the following additions only
when enabling linting.

Keep linting intentionally simple:

- Python: [`ruff`][ruff]
- Types: [`ty`][ty]
- Markdown: [`mdformat`][mdformat]
- One entry point: `make lint`

## Needed additions

Add dev tools to root `pyproject.toml`:

```bash
uv add --dev ruff ty mdformat pre-commit
```

Add one lint command to the root `Makefile` and use it for local + CI:

```makefile
lint: ## Lint project
  uv run ruff check --fix .
  uv run ruff format .
  uv run ty check .
  uv run mdformat --wrap 100 .
```

## `pyproject.toml` config additions

```toml
[tool.ruff]
src = ["src/**/src"]
line-length = 100
target-version = "py313"
show-fixes = true
lint.select = [
    "B0",     # bugbear
    "E",      # pycodestyle
    "F",      # Pyflakes
    "I",      # import order
    "UP",     # pyupgrade
    "RUF100", # valid noqa annotations
]
```

## Optional pre-commit (single step)

If you use [pre-commit], keep it as a single hook that delegates to Make:

```yaml
repos:
  - repo: local
    hooks:
      - id: make-lint
        name: make lint
        entry: make lint
        language: system
        pass_filenames: false
```

This keeps `make lint` as the single source of truth for lint behavior.

## AGENTS.md section

Append to project `AGENTS.md`:

```markdown
## Linting

`make lint` runs ruff, ty, and mdformat. Config in root `pyproject.toml`.
```

## Verify

All three must exit 0. Re-run `make lint` after fixes — ruff auto-fixes most issues on first pass.

```bash
make lint                    # ruff, ty, mdformat run clean
make run pkg=<package_name>  # core still works
make test
```

[mdformat]: https://mdformat.readthedocs.io/
[pre-commit]: https://pre-commit.com/
[ruff]: https://docs.astral.sh/ruff/
[ty]: https://docs.astral.sh/ty/
