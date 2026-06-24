---
name: "prefect"
description: "Prefect is a modern workflow orchestration framework for Python data pipelines. Learn to define flows and tasks with decorators, handle retries and scheduling, create deployments, and monitor via the Prefect UI."
metadata:
  category: data
  source:
    repository: "https://github.com/TerminalSkills/skills"
    path: "skills/prefect"
    license_path: "LICENSE"
---

# Prefect

Prefect turns Python functions into observable, schedulable workflows with minimal boilerplate. Add `@flow` and `@task` decorators to get retries, logging, caching, and a monitoring UI.

## Installation

```bash
# Install Prefect
pip install prefect

# Start the local Prefect server (UI + API)
prefect server start
# UI at http://localhost:4200

# Or use Prefect Cloud (managed)
prefect cloud login
```

## Basic Flow

```python
# flows/hello.py: Simple flow with tasks
from prefect import flow, task, get_run_logger
from datetime import timedelta

@task(retries=3, retry_delay_seconds=10)
def fetch_data(url: str) -> dict:
    import httpx
    logger = get_run_logger()
    logger.info(f"Fetching {url}")
    response = httpx.get(url)
    response.raise_for_status()
    return response.json()

@task(cache_expiration=timedelta(hours=1))
def transform(data: dict) -> list:
    return [
        {"id": item["id"], "value": item["amount"] * 100}
        for item in data["results"]
    ]

@task
def load(records: list) -> int:
    logger = get_run_logger()
    logger.info(f"Loading {len(records)} records")
    # Insert into database...
    return len(records)

@flow(name="etl-pipeline", log_prints=True)
def etl_pipeline(api_url: str = "https://api.example.com/data"):
    raw = fetch_data(api_url)
    cleaned = transform(raw)
    count = load(cleaned)
    print(f"Processed {count} records")
    return count

if __name__ == "__main__":
    etl_pipeline()
```

## Scheduling and Deployments

```python
# flows/deploy.py: Create a deployment with schedule
from prefect import flow
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule

@flow
def daily_report():
    print("Generating daily report...")

if __name__ == "__main__":
    # Deploy via Python
    daily_report.serve(
        name="daily-report-deployment",
        cron="0 8 * * *",  # Every day at 8 AM
        tags=["reporting"],
        parameters={"param1": "value1"},
    )
```

```bash
# deploy.sh: Deploy and manage via CLI
# Create deployment from flow file
prefect deploy flows/hello.py:etl_pipeline \
  --name etl-prod \
  --pool default-agent-pool \
  --cron "*/30 * * * *"

# Start a worker to execute deployments
prefect worker start --pool default-agent-pool

# Trigger a deployment run
prefect deployment run "etl-pipeline/etl-prod" --param api_url=https://api.example.com
```

## Error Handling and Concurrency

```python
# flows/advanced.py: Concurrent tasks, error handling, and sub-flows
from prefect import flow, task
from prefect.tasks import task_input_hash
import asyncio

@task(
    retries=2,
    retry_delay_seconds=[10, 60],  # Exponential backoff
    cache_key_fn=task_input_hash,
    timeout_seconds=300,
)
def process_item(item_id: int) -> dict:
    # Process a single item
    return {"id": item_id, "status": "done"}

@flow
def batch_process(item_ids: list[int]):
    # Submit tasks concurrently
    futures = [process_item.submit(id) for id in item_ids]
    results = [f.result() for f in futures]

    succeeded = [r for r in results if r["status"] == "done"]
    print(f"Processed {len(succeeded)}/{len(item_ids)} items")

@flow
async def async_pipeline():
    # Async flow for I/O-bound work
    results = await asyncio.gather(
        fetch_from_api("source_a"),
        fetch_from_api("source_b"),
    )
    return results
```

## Blocks and Infrastructure

```python
# flows/blocks.py: Use blocks for reusable configuration
from prefect.blocks.system import Secret, JSON
from prefect_sqlalchemy import SqlAlchemyConnector

# Store secrets (set via UI or CLI)
# prefect block register -m prefect_sqlalchemy
# Then configure in UI at http://localhost:4200/blocks

# Use in flows
@flow
def db_flow():
    api_key = Secret.load("my-api-key").get()
    config = JSON.load("pipeline-config").value

    with SqlAlchemyConnector.load("prod-db") as conn:
        result = conn.fetch_all("SELECT count(*) FROM users")
        print(result)
```

## Notifications

```python
# flows/notifications.py: Send alerts on failure
from prefect import flow
from prefect.blocks.notifications import SlackWebhook

@flow
def monitored_flow():
    try:
        # ... do work
        pass
    except Exception as e:
        slack = SlackWebhook.load("alerts-channel")
        slack.notify(f"❌ Pipeline failed: {e}")
        raise

# Or use automations in Prefect UI:
# Automations → Create → Trigger: Flow run failed → Action: Send Slack notification
```

## CLI Reference

```bash
# cli.sh: Common Prefect CLI commands
# Check connection
prefect version
prefect config view

# List flows and deployments
prefect flow-run ls
prefect deployment ls

# View logs
prefect flow-run logs <flow-run-id>

# Manage work pools
prefect work-pool create my-pool --type process
prefect work-pool ls
```
