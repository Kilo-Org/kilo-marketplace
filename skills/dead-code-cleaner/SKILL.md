---
name: dead-code-cleaner
description: >-
  This skill should be used when the user wants to identify and safely remove
  dead code from a codebase. It provides systematic procedures for detecting
  unused imports, functions, variables, exports, unreachable code, and other
  dead code patterns across multiple programming languages with verification
  steps to ensure safe removal.
license: Apache 2.0
metadata:
  category: development
  author: kilo-marketplace
  version: 1.0.0
---

# Dead Code Cleaner

This skill provides a systematic approach to identifying and removing dead code from codebases while ensuring safety through verification steps.

## When to Use

Use this skill when:
- The user wants to clean up or optimize a codebase
- The user asks about removing unused code, imports, or exports
- The user wants to reduce bundle size or improve code maintainability
- The user mentions "dead code", "unused code", or "code cleanup"

## Dead Code Categories

### 1. Unused Imports
- Import statements that are never referenced in the code
- Default imports that are not used
- Named imports that are never utilized
- Side-effect only imports that may be unnecessary

### 2. Unused Functions and Methods
- Private functions that are never called
- Public functions that have no consumers
- Class methods that are never invoked
- Arrow functions and function expressions without references

### 3. Unused Variables
- Declared variables that are never read
- Constants that are defined but not used
- Let variables that are assigned but never consumed
- Destructured variables that are ignored

### 4. Unused Exports
- Exported functions, classes, or constants with no external consumers
- Re-exports that duplicate existing exports
- Default exports that are never imported elsewhere
- Named exports without any usage

### 5. Unreachable Code
- Code after return, throw, break, or continue statements
- Code in branches that can never be true
- Dead branches in conditional statements
- Unused catch blocks

### 6. Unused Type Definitions
- TypeScript interfaces that are never implemented or referenced
- Type aliases without usage
- Unused generic type parameters
- Deprecated type declarations

### 7. Unused Files
- Files that are not imported anywhere
- Orphaned test files
- Unused configuration files
- Legacy files that are no longer referenced

## Language-Specific Detection

### JavaScript/TypeScript

**Tools:**
- ESLint with `no-unused-vars` rule
- TypeScript compiler with `noUnusedLocals` and `noUnusedParameters`
- `ts-prune` for finding unused exports
- `depcheck` for unused dependencies

**Detection Commands:**
```bash
# TypeScript unused checks
npx tsc --noUnusedLocals --noUnusedParameters

# Find unused exports
npx ts-prune

# Check for unused dependencies
npx depcheck
```

**Common Patterns to Check:**
- `import { unused } from 'module'`
- `const unused = require('module')`
- `export function unusedFn() {}`
- `interface UnusedInterface {}`

### Python

**Tools:**
- `pylint` with various checks
- `vulture` for finding dead code
- `autoflake` for removing unused imports
- `pyflakes` for quick checks

**Detection Commands:**
```bash
# Find dead code
vulture src/

# Check for unused imports
pyflakes src/

# Remove unused imports automatically
autoflake --check -r src/
```

**Common Patterns to Check:**
- `from module import unused`
- `import unused_module`
- `def unused_function():`
- `class UnusedClass:`

### Java

**Tools:**
- IntelliJ IDEA built-in analysis
- Eclipse compiler warnings
- PMD with `UnusedLocalVariable`, `UnusedPrivateMethod` rules
- SpotBugs for bytecode analysis

**Common Patterns to Check:**
- Private methods with no callers
- Unused private fields
- Unused imports
- Unreachable catch blocks

### Go

**Tools:**
- `go vet` for basic checks
- `staticcheck` for comprehensive analysis
- `deadcode` tool
- Built-in unused variable detection

**Detection Commands:**
```bash
# Built-in check
go vet ./...

# Static analysis
staticcheck ./...

# Find unused code
deadcode ./...
```

### Rust

**Tools:**
- `cargo clippy` with dead_code lint
- Built-in compiler warnings
- `cargo-udeps` for unused dependencies

**Detection Commands:**
```bash
# Check for dead code
cargo clippy -- -W dead_code

# Find unused dependencies
cargo +nightly udeps
```

## Safe Removal Workflow

### Phase 1: Analysis

1. **Create a backup or branch**
   ```bash
   git checkout -b cleanup/dead-code-removal
   ```

2. **Run detection tools**
   - Execute language-specific detection commands
   - Record all findings in a report
   - Categorize findings by type and risk level

3. **Generate analysis report**
   - List all detected dead code
   - Include file paths and line numbers
   - Note any ambiguous cases

### Phase 2: Verification

1. **Cross-reference with tests**
   - Check if code is used in test files
   - Verify no dynamic imports or reflection usage
   - Check for string-based references (e.g., dependency injection)

2. **Search for indirect usage**
   ```bash
   # Search for string references
   grep -r "functionName" --include="*.{js,ts,jsx,tsx}"
   
   # Search in configuration files
   grep -r "functionName" --include="*.{json,yaml,yml,xml}"
   ```

3. **Check for dynamic patterns**
   - Reflection-based calls
   - Dependency injection containers
   - Plugin/extension systems
   - Configuration-driven code execution

4. **Verify export usage across packages**
   - Check all consuming packages
   - Verify no external API consumers
   - Review published package exports

### Phase 3: Removal

1. **Start with low-risk items**
   - Unused imports (lowest risk)
   - Unused private variables
   - Unused private methods

2. **Progress to higher-risk items**
   - Unused exports (verify no external consumers)
   - Unused public functions
   - Unused files

3. **Apply changes incrementally**
   - Make one logical change at a time
   - Run tests after each change
   - Commit frequently with descriptive messages

### Phase 4: Validation

1. **Run full test suite**
   ```bash
   # Run all tests
   npm test  # or equivalent
   
   # Run with coverage
   npm test -- --coverage
   ```

2. **Build the project**
   ```bash
   # Production build
   npm run build
   ```

3. **Run linting**
   ```bash
   npm run lint
   ```

4. **Verify no runtime errors**
   - Start development server
   - Check critical user flows
   - Verify no console errors

## Risk Assessment Matrix

| Code Type | Risk Level | Verification Required |
|-----------|------------|----------------------|
| Unused imports | Low | Basic search |
| Unused private variables | Low | Class/file search |
| Unused private methods | Low-Medium | Full project search |
| Unused exports | Medium | Cross-package search |
| Unused public functions | Medium-High | Full codebase + external check |
| Unused files | High | Comprehensive search + config check |
| Unreachable code | Low | Control flow analysis |

## Special Considerations

### Framework-Specific Patterns

**React:**
- Exported components may appear unused to basic static analysis but are consumed via JSX
- Higher-order components may reference components dynamically
- Check for usage in route configurations

**Angular:**
- Decorators may register components/services dynamically
- Check module declarations and providers
- Verify no lazy-loaded module references

**Vue:**
- Component registration may be global
- Check for dynamic component names
- Verify usage in templates

**Spring (Java):**
- Beans may be auto-wired by type
- Check for component scanning
- Verify no reflection-based usage

### Dynamic Code Patterns

Be cautious with:
- `eval()` and `new Function()` usage
- Dynamic imports: `import()`
- Reflection and introspection
- Plugin architectures
- Configuration-driven code
- Code generation patterns

## Example Session

```
User: Clean up the dead code in my TypeScript project

Agent: I'll help you clean up dead code in your TypeScript project. Let me follow the systematic approach:

## Phase 1: Analysis

First, let me create a cleanup branch and run detection tools:

[Creates branch and runs analysis]

I found the following dead code:
- 15 unused imports across 8 files
- 3 unused private methods
- 2 unused exports
- 1 unreachable code block

## Phase 2: Verification

Let me verify these findings by checking for dynamic usage...

[Performs verification]

All items verified as safe to remove except:
- `exportHelper.ts` - may be used by external packages

## Phase 3: Removal

Starting with low-risk items...

[Removes code incrementally with commits]

## Phase 4: Validation

Running tests and build...

[Validates changes]

✅ All tests pass
✅ Build successful
✅ No lint errors

Summary: Removed 15 unused imports, 3 unused methods, 1 unreachable block.
```

## Output Artifacts

When running this skill, produce:
1. **Analysis Report** (`dead-code-analysis.md`) - List of all detected dead code
2. **Removal Log** - Changes made with justification
3. **Verification Checklist** - Completed verification steps
