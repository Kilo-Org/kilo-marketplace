# Husky v9+ Setup

Quick setup using `husky init`:

```bash
# Install and initialize in one command
npm install --save-dev husky && npx husky init
```

This automatically:
- Creates `.husky/` directory
- Adds `"prepare": "husky"` script to package.json
- Creates `.husky/pre-commit` hook file

## Add commands to pre-commit hook

Edit `.husky/pre-commit` and add your commands:

```bash
# Example: run lint and tests
npm run lint
npm test
```

## Verify

```bash
# Test that the hook works
git commit -m "Test husky hook"
```

## Key points

- v9+ uses `npx husky init` (not `husky install` or `husky add`)
- Hooks are just shell scripts in `.husky/` directory
- No shebang or husky.sh sourcing needed
- The `prepare` script runs automatically after `npm install`
