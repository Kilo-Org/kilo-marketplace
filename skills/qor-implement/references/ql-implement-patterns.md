# QL Implement Patterns and Templates

This reference contains code patterns and templates used by /ql-implement.

## TDD-Light Test Template

```typescript
// tests/[feature].test.ts

describe('[Feature Name]', () => {
  it('should [single success condition from blueprint]', () => {
    // Arrange
    const input = [test input];

    // Act
    const result = featureFunction(input);

    // Assert
    expect(result).toBe([expected from blueprint]);
  });
});
```

## Section 4 Razor Checklist

```markdown
## Section 4 Razor Checklist

### Function-Level (Micro KISS)
- [ ] Lines <= 40
- [ ] Nesting <= 3 levels
- [ ] No nested ternaries
- [ ] Variables are noun/verbNoun (no x, data, obj)
- [ ] Early returns to flatten logic
- [ ] Classifiable as semantic (pure) or pragmatic (orchestrator)
- [ ] Semantic: no side effects, no comments needed
- [ ] Pragmatic: has doc comments noting unexpected behaviors

### File-Level (Macro KISS)
- [ ] Total lines <= 250
- [ ] Single responsibility
- [ ] No "God Object" patterns
- [ ] Clear module boundaries

### Model-Level (Type Safety)
- [ ] Enums over optional fields for mutually exclusive states
- [ ] Brand types for domain primitives (not bare String/Uuid)
- [ ] Model name indicates field membership
- [ ] Composition over flattening for independent concepts
```

## Code Patterns

### Nesting Flattening

```typescript
// BEFORE (4 levels - VIOLATION)
function process(data) {
  if (data) {
    if (data.items) {
      for (const item of data.items) {
        if (item.valid) {
          // logic
        }
      }
    }
  }
}

// AFTER (2 levels - COMPLIANT)
function process(data) {
  if (!data || !data.items) return;

  const validItems = data.items.filter(item => item.valid);
  validItems.forEach(processItem);
}

function processItem(item) {
  // logic
}
```

### Explicit Naming

```typescript
// BEFORE (generic - VIOLATION)
const x = getData();
const result = process(x);

// AFTER (explicit - COMPLIANT)
const userPreferences = fetchUserPreferences();
const validatedPreferences = validatePreferences(userPreferences);
```

### Dependency Diet

```typescript
// BEFORE using lodash.get
import { get } from 'lodash';
const value = get(obj, 'a.b.c');

// AFTER (vanilla - 3 lines)
const safeGet = (obj, path) =>
  path.split('.').reduce((o, k) => (o ? o[k] : undefined), obj);
const value = safeGet(obj, 'a.b.c');
```

## Visual Silence Examples

```css
/* VIOLATION */
.button {
  color: #ff0000;
  background: blue;
  padding: 16px;
}

/* COMPLIANT */
.button {
  color: var(--color-error);
  background: var(--background-primary);
  padding: var(--spacing-md);
}
```

```typescript
// VIOLATION - onClick with no handler
<button>Submit</button>

// COMPLIANT - explicit handler
<button onClick={handleFormSubmit}>Submit</button>
```

## Cleanup Checklist

```markdown
### Cleanup Checklist
- [ ] Remove all console.log statements
- [ ] Remove commented-out code
- [ ] Remove unrequested configuration options
- [ ] Final variable rename pass
- [ ] Verify no YAGNI violations (features not in blueprint)
```

## Implementation Complete Report

```markdown
## Implementation Complete

**Files Created/Modified**:
| File | Lines | Max Nesting | Status |
|------|-------|-------------|--------|
| [path] | [count]/250 | [depth]/3 | OK |

**Tests**:
| Test File | Passing |
|-----------|---------|
| [path] | [yes/no] |

**Section 4 Razor Compliance**: VERIFIED

### Next Action
Implementation complete. The Judge must now invoke `/ql-substantiate` to verify and seal.

---

_Reality built. Awaiting substantiation._
```
