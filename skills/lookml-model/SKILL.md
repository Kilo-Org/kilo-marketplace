---
name: lookml-model
description: >-
  Use this skill when you need to create or modify a LookML Model file
  (.model.lkml). This includes defining connections, includes, and configuring
  model-level settings.
metadata:
  category: data
  source:
    repository: 'https://github.com/looker-open-source/looker-skills'
    path: skills/lookml-model
    license_path: LICENSE
    commit: c530d1b7efee1db49851a04563ce946adfd191a8
---

# Instructions

1.  **Define the Model File**: A model file generally corresponds to a single database connection and includes Explores.
2.  **Required Parameters**:
    - `connection: "connection_name"`: Must match a connection defined in Looker Admin.
    - `include: "pattern"`: Specifies which view and dashboard files are available to the model.
3.  **Best Practices**:
    - **Includes**: Avoid `include: "*.view"` if possible to prevent performance issues and namespace clutter. Use specific paths or wildcards like `include: "/views/users.view"` or `include: "/views/marketing/*.view"`.
    - **Label**: Use `label:` to provide a user-friendly name for the model in the UI.
    - **Week Start Day**: Set `week_start_day:` if the business logic requires a specific start day (e.g., `monday`).
    - **Datagroups & Caching**: ALWAYS use datagroups for caching policies to align Looker with your ETL/ELT processes.

## 4. Datagroups & Caching

Datagroups are the preferred mechanism for managing caching policies.

- **Definition**: Define in the model file.
- **sql_trigger**: A query that returns a single value (e.g., max timestamp). If the value changes, the cache is invalidated.
- **max_cache_age**: A fallback duration if the trigger doesn't change.
- **persist_with**: Apply the datagroup to Explores or the entire model.

### Datagroups vs `persist_for`

| Feature        | Datagroups (Recommended)                   | `persist_for`                         |
| :------------- | :----------------------------------------- | :------------------------------------ |
| **Trigger**    | SQL Query (Smart)                          | Fixed Time (Dumb)                     |
| **Alignment**  | Aligns with ETL/ELT completion             | Misaligned (guesswork)                |
| **Management** | Centralized in Model file                  | Scattered in Explores/Models          |
| **Use Case**   | Production dashboards, ETL synchronization | Ad-hoc queries, Real-time (<1h) needs |

> [!TIP]
> Use `persist_for` ONLY for real-time dashboards where you need to force a cache refresh every X minutes (e.g., stock tickers, fast-moving inventory). For everything else, use **Datagroups**.

## 5. Include Patterns

Use strict patterns to control scope and performance.

| Pattern | Description | Use Case |
| :--- | :--- | :--- |
| `include: "/views/*.view"` | All views in specific folder | Standard modularity |
| `include: "/views/marketing/users.view"` | Specific file | Precise control, avoids conflicts |
| `include: "/**/*.view"` | **Recursive** (all views in project) | **Avoid** unless small project |
| `include: "/dashboards/*.dashboard"` | All dashboards in folder | Importing dashboards |

# Examples

## Basic Model

```lookml
connection: "thelook"

# Include all views in the views/ folder
include: "/views/*.view"

# Include all dashboards
include: "/*.dashboard"

# Define an Explore (usually better to define in separate files for large projects, but acceptable here for small ones)
explore: orders {
  join: users {
    type: left_outer
    sql_on: ${orders.user_id} = ${users.id} ;;
    relationship: many_to_one
  }
}
```

## Model with Specific Settings

````lookml
connection: "snowlooker"

label: "eCommerce Analytics"

# Set valid week start day
week_start_day: monday

# Include specific folders
include: "/views/finance/*.view"
include: "/views/marketing/*.view"

## Model with Datagroup (Best Practice)

```lookml
connection: "thelook"

# Define the caching policy
datagroup: ecommerce_etl {
  description: "Triggers when the max created_at date changes in the events table."
  sql_trigger: SELECT MAX(created_at) FROM `project.dataset.events` ;;
  max_cache_age: "24 hours" # Fallback
}

# Apply default caching to all Explores in this model
persist_with: ecommerce_etl

include: "/views/*.view"

explore: orders {
  # This explore inherits 'persist_with: ecommerce_etl' from the model default
}

explore: real_time_dashboard {
  # Override with a different policy if needed
  persist_for: "5 minutes"
}
```
