# QL Refactor Examples and Templates

This reference contains the example transformations and report templates used by /ql-refactor.

## Function Decomposition Example

```typescript
// BEFORE: 60-line monolith
function processOrder(order) {
  // validation (15 lines)
  // ...
  // transformation (20 lines)
  // ...
  // persistence (15 lines)
  // ...
  // notification (10 lines)
  // ...
}

// AFTER: Specialized sub-functions
function processOrder(order) {
  const validatedOrder = validateOrder(order);
  const transformedOrder = transformOrder(validatedOrder);
  const savedOrder = persistOrder(transformedOrder);
  notifyOrderComplete(savedOrder);
  return savedOrder;
}

function validateOrder(order) {
  /* 15 lines */
}
function transformOrder(order) {
  /* 20 lines */
}
function persistOrder(order) {
  /* 15 lines */
}
function notifyOrderComplete(order) {
  /* 10 lines */
}
```

## Logic Flattening Example

```typescript
// BEFORE: 4 levels (VIOLATION)
function getUser(id) {
  if (id) {
    const user = db.find(id);
    if (user) {
      if (user.active) {
        if (user.verified) {
          return user;
        }
      }
    }
  }
  return null;
}

// AFTER: 1 level (COMPLIANT)
function getUser(id) {
  if (!id) return null;

  const user = db.find(id);
  if (!user) return null;
  if (!user.active) return null;
  if (!user.verified) return null;

  return user;
}
```

## Ternary Elimination Example

```typescript
// BEFORE: Nested ternary (VIOLATION)
const status = isActive
  ? (isPremium ? "active-premium" : "active-basic")
  : "inactive";

// AFTER: Explicit logic (COMPLIANT)
function getStatus(isActive, isPremium) {
  if (!isActive) return "inactive";
  return isPremium ? "active-premium" : "active-basic";
}
const status = getStatus(isActive, isPremium);
```

## Variable Renaming Examples

| Generic (BAD) | Explicit (GOOD)      |
| ------------- | -------------------- |
| `x`           | `userCount`          |
| `data`        | `responsePayload`    |
| `obj`         | `configOptions`      |
| `temp`        | `intermediateResult` |
| `item`        | `orderLineItem`      |
| `result`      | `validationOutcome`  |

## Orphan Detection Report (Template)

```markdown
### Orphan Detection Report

| File   | Connected   | Import Chain        |
| ------ | ----------- | ------------------- |
| [path] | OK          | main -> App -> [file] |
| [path] | FAIL ORPHAN | No import found     |
```

## File Splitting Example

```
BEFORE:
src/utils.ts (400 lines)
  - stringHelpers (80 lines)
  - dateHelpers (120 lines)
  - validationHelpers (100 lines)
  - formatters (100 lines)

AFTER:
src/utils/
  - index.ts (re-exports)
  - stringHelpers.ts (80 lines)
  - dateHelpers.ts (120 lines)
  - validationHelpers.ts (100 lines)
  - formatters.ts (100 lines)
```

## God Object Elimination Example

```typescript
// BEFORE: God Object
class UserManager {
  // User CRUD (should be UserRepository)
  createUser() {}
  getUser() {}
  updateUser() {}
  deleteUser() {}

  // Authentication (should be AuthService)
  login() {}
  logout() {}
  validateToken() {}

  // Email (should be EmailService)
  sendWelcome() {}
  sendPasswordReset() {}
}

// AFTER: Single Responsibility
class UserRepository {
  /* CRUD only */
}
class AuthService {
  /* auth only */
}
class EmailService {
  /* email only */
}
```

## Dependency Audit (Template)

```markdown
### Dependency Audit

| Package | Used | Vanilla Possible | Recommendation  |
| ------- | ---- | ---------------- | --------------- |
| lodash  | OK   | Yes (3 lines)    | REMOVE          |
| dayjs   | OK   | No               | KEEP            |
| uuid    | FAIL | N/A              | REMOVE (unused) |
```

## Section 4 Compliance Report (Template)

```markdown
### Section 4 Razor Compliance After Refactor

| File   | Lines   | Max Function | Max Nesting | Status |
| ------ | ------- | ------------ | ----------- | ------ |
| [path] | [X]/250 | [X]/40       | [X]/3       | OK/FAIL |
```

## Ledger Entry (Template)

```markdown
---

### Entry #[N]: REFACTOR

**Timestamp**: [ISO 8601]
**Phase**: IMPLEMENT (refactor)
**Author**: Specialist
**Scope**: [single-file / multi-file]

**Changes**:
- [summary of changes]

**Content Hash**:
```
SHA256(modified files)
= [hash]
```

**Previous Hash**: [from entry N-1]

**Chain Hash**:
```
SHA256(content_hash + previous_hash)
= [calculated]
```

**Decision**: KISS refactor complete. Section 4 compliance verified.
```

## Handoff Report (Template)

```markdown
## Refactor Complete

**Scope**: [file or directory]
**Violations Fixed**: [count]
**Files Modified**: [count]

### Changes Summary

| Change Type          | Count |
| -------------------- | ----- |
| Functions split      | [X]   |
| Nesting flattened    | [X]   |
| Variables renamed    | [X]   |
| Files split          | [X]   |
| Orphans removed      | [X]   |
| Dependencies removed | [X]   |

### Next Action

The Judge should invoke `/ql-substantiate` to verify and seal.

---

_Simplification complete. Awaiting substantiation._
```
