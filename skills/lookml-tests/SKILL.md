---
name: lookml-tests
description: >-
  Standards and best practices for writing LookML tests to ensure data
  integrity, accuracy, and logic validation.
metadata:
  category: data
  source:
    repository: 'https://github.com/looker-open-source/looker-skills'
    path: skills/lookml-tests
    license_path: LICENSE
    commit: c530d1b7efee1db49851a04563ce946adfd191a8
---

# LookML Testing Standards

Testing is critical for maintaining trust in data. LookML tests allow us to verify that our semantic model behaves as expected and that the underlying data conforms to our assumptions.

## 1. File Organization

-   **Location**: Define tests in `tests/[explore_name].test.lkml`.
-   **One Suite Per Explore**: Each file should contain *all* the test definitions for a specific Explore.
-   **Naming Convention**: `[explore_name].test.lkml` (e.g., `orders.test.lkml`).

## 2. Test Structure

Each test consists of an `explore_source` query and an `assert` statement.

```lookml
test: [test_name] {
  explore_source: [explore_name] {
    column: [column_name] { field: [view_name].[field_name] }
    filters: {
      field: [view_name].[field_name]
      value: "[value]"
    }
  }

  assert: [assertion_name] {
    expression: ${[view_name].[field_name]} [operator] [value] ;;
  }
}
```

## 3. Types of Tests

### A. Integrity Checks (Critical)
Verify that Primary Keys remain unique after joins. This is the best defense against "fanout" errors caused by incorrect `one_to_many` join definitions.

**Example: Primary Key Uniqueness**
```lookml
test: orders_pk_is_unique {
  explore_source: orders {
    column: order_id {}
    column: count {}
    # Limit to recent data to save costs/time if table is large
    filters: {
      field: orders.created_date
      value: "last 7 days"
    }
  }

  assert: order_id_is_unique {
    expression: ${orders.count} = 1 ;;
  }
}
```

### B. Accuracy Tests
Validate specific measure values against known constants or expectations.

**Example: Revenue is Positive**
```lookml
test: revenue_is_positive {
  explore_source: orders {
    column: total_revenue {}
    filters: {
      field: orders.created_date
      value: "yesterday"
    }
  }

  assert: revenue_greater_than_zero {
    expression: ${orders.total_revenue} >= 0 ;;
  }
}
```

### C. Business Logic Validation
Ensure calculations behave as expected. For example, checking that `gross_margin` is never greater than `revenue` or that `lifetime_orders` is never NULL for an active user.

**Example: Logic Check**
```lookml
test: margin_less_than_revenue {
  explore_source: orders {
    column: total_revenue {}
    column: total_margin {}
  }

  assert: margin_is_valid {
    expression: ${orders.total_margin} <= ${orders.total_revenue} ;;
  }
}
```

## 4. Best Practices

-   **Descriptive Extensions**: Use informative names for tests (`orders_pk_is_unique`) and assertions (`order_id_is_unique`).
-   **Performance**: Use filters (e.g., `last 7 days`) to limit the scan size for large tables, unless verifying full history is required.
-   **Model Inclusion**: Ensure `test` files are included in the model file (e.g., `include: "/tests/*.test.lkml"`).
