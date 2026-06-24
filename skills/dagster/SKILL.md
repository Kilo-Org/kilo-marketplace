---
name: "dagster"
description: "Dagster is a data pipeline orchestrator built around the concept of software-defined assets. Learn to define assets, ops, jobs, schedules, sensors, and resources for building maintainable data platforms."
metadata:
  category: data
  source:
    repository: "https://github.com/TerminalSkills/skills"
    path: "skills/dagster"
    license_path: "LICENSE"
---

# Dagster

Dagster organizes data pipelines around software-defined assets — declarations of the data artifacts your pipeline produces. Assets track lineage, enable incremental computation, and integrate with the Dagster UI.

## Installation

```bash
# Install Dagster and UI
pip install dagster dagster-webserver

# Create a new project
dagster project scaffold --name my_pipeline
cd my_pipeline
pip install -e ".[dev]"

# Start the dev server
dagster dev
# UI at http://localhost:3000
```

## Software-Defined Assets

```python
# my_pipeline/assets.py: Define assets that produce data
from dagster import asset, AssetExecutionContext
import pandas as pd

@asset(group_name="raw")
def raw_users(context: AssetExecutionContext) -> pd.DataFrame:
    """Fetch raw user data from API."""
    import httpx
    response = httpx.get("https://api.example.com/users")
    df = pd.DataFrame(response.json())
    context.log.info(f"Fetched {len(df)} users")
    return df

@asset(group_name="raw")
def raw_orders(context: AssetExecutionContext) -> pd.DataFrame:
    """Fetch raw order data from API."""
    import httpx
    response = httpx.get("https://api.example.com/orders")
    return pd.DataFrame(response.json())

@asset(group_name="analytics", deps=[raw_users, raw_orders])
def revenue_by_user(raw_users: pd.DataFrame, raw_orders: pd.DataFrame) -> pd.DataFrame:
    """Calculate total revenue per user."""
    merged = raw_orders.merge(raw_users, left_on="user_id", right_on="id")
    result = (
        merged.groupby(["user_id", "name"])
        .agg(total_revenue=("amount", "sum"), order_count=("id_x", "count"))
        .reset_index()
    )
    return result
```

## Resources

```python
# my_pipeline/resources.py: Configurable resources for external systems
from dagster import resource, ConfigurableResource
import sqlalchemy

class DatabaseResource(ConfigurableResource):
    connection_string: str

    def query(self, sql: str) -> list:
        engine = sqlalchemy.create_engine(self.connection_string)
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text(sql))
            return [dict(row._mapping) for row in result]

    def execute(self, sql: str):
        engine = sqlalchemy.create_engine(self.connection_string)
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text(sql))
            conn.commit()
```

## Assets with Resources

```python
# my_pipeline/db_assets.py: Assets that use database resources
from dagster import asset, AssetExecutionContext
from .resources import DatabaseResource

@asset(group_name="warehouse")
def dim_users(context: AssetExecutionContext, database: DatabaseResource):
    """Load cleaned user dimension table into warehouse."""
    users = database.query("SELECT id, name, email, created_at FROM raw_users")
    context.log.info(f"Loaded {len(users)} users into warehouse")
    return users
```

## Definitions

```python
# my_pipeline/__init__.py: Wire everything together
from dagster import Definitions, load_assets_from_modules
from . import assets, db_assets
from .resources import DatabaseResource

all_assets = load_assets_from_modules([assets, db_assets])

defs = Definitions(
    assets=all_assets,
    resources={
        "database": DatabaseResource(
            connection_string="postgresql://user:pass@localhost:5432/analytics"
        ),
    },
)
```

## Schedules and Sensors

```python
# my_pipeline/schedules.py: Time-based and event-based triggers
from dagster import (
    ScheduleDefinition,
    define_asset_job,
    sensor,
    RunRequest,
    SensorEvaluationContext,
    AssetSelection,
)

# Job that materializes specific assets
analytics_job = define_asset_job(
    name="analytics_job",
    selection=AssetSelection.groups("analytics"),
)

# Cron schedule
daily_analytics = ScheduleDefinition(
    job=analytics_job,
    cron_schedule="0 6 * * *",  # 6 AM daily
)

# Sensor — trigger on external event
@sensor(job=analytics_job, minimum_interval_seconds=60)
def new_file_sensor(context: SensorEvaluationContext):
    import os
    files = os.listdir("/data/incoming")
    new_files = [f for f in files if f.endswith(".csv")]
    if new_files:
        context.log.info(f"Found {len(new_files)} new files")
        yield RunRequest(run_key=new_files[0])
```

## Partitioned Assets

```python
# my_pipeline/partitioned.py: Time-partitioned assets for incremental processing
from dagster import asset, DailyPartitionsDefinition

daily_partitions = DailyPartitionsDefinition(start_date="2026-01-01")

@asset(partitions_def=daily_partitions, group_name="raw")
def daily_events(context):
    """Fetch events for a specific date partition."""
    date = context.partition_key  # e.g., "2026-02-19"
    context.log.info(f"Processing events for {date}")
    # Fetch only this date's data
    return fetch_events(date)
```

## CLI Reference

```bash
# cli.sh: Common Dagster CLI commands
# Development server
dagster dev

# Materialize assets
dagster asset materialize --select raw_users,raw_orders

# List assets
dagster asset list

# Run a job
dagster job execute -j analytics_job

# Check definitions
dagster definitions validate
```
