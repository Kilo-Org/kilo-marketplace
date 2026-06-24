---
name: "azure-eventhub-py"
description: "Azure Event Hubs SDK for Python streaming. Use for high-throughput event ingestion, producers, consumers, and checkpointing. Triggers: \"event hubs\", \"EventHubProducerClient\", \"EventHubConsumerClient\", \"streaming\", \"partitions\"."
metadata:
  category: data
  source:
    repository: "https://github.com/microsoft/skills"
    path: ".github/plugins/azure-sdk-python/skills/azure-eventhub-py"
    license_path: "LICENSE"
---

# Azure Event Hubs SDK for Python

Big data streaming platform for high-throughput event ingestion.

## Installation

```bash
pip install azure-eventhub azure-identity
# For checkpointing with blob storage
pip install azure-eventhub-checkpointstoreblob-aio
```

## Environment Variables

```bash
EVENT_HUB_FULLY_QUALIFIED_NAMESPACE=<namespace>.servicebus.windows.net  # Required for all auth methods
EVENT_HUB_NAME=my-eventhub  # Required for all auth methods
STORAGE_ACCOUNT_URL=https://<account>.blob.core.windows.net  # Required for checkpoint storage
CHECKPOINT_CONTAINER=checkpoints  # Required for checkpoint storage
AZURE_TOKEN_CREDENTIALS=prod # Required only if DefaultAzureCredential is used in production
```

## Authentication & Lifecycle

> **🔑 Two rules apply to every code sample below:**
>
> 1. **Prefer `DefaultAzureCredential`.** It works locally (Azure CLI / VS Code / Developer CLI) and in Azure (managed identity, workload identity) with no code change. Avoid connection strings, account/API keys — they bypass Entra audit and rotation.
>    - Local dev: `DefaultAzureCredential` works as-is.
>    - Production: set `AZURE_TOKEN_CREDENTIALS=prod` (or `AZURE_TOKEN_CREDENTIALS=<specific_credential>`) to constrain the credential chain to production-safe credentials.
> 2. **Wrap every client in a context manager** so HTTP transports, sockets, and token caches are released deterministically:
>    - Sync: `with <Client>(...) as client:`
>    - Async: `async with <Client>(...) as client:` **and** `async with DefaultAzureCredential() as credential:` (from `azure.identity.aio`)
>
> Snippets may abbreviate this setup, but production code should always follow both rules.

```python
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.eventhub import EventHubProducerClient, EventHubConsumerClient

# Local dev: DefaultAzureCredential. Production: set AZURE_TOKEN_CREDENTIALS=prod or AZURE_TOKEN_CREDENTIALS=<specific_credential>
credential = DefaultAzureCredential(require_envvar=True)
# Or use a specific credential directly in production:
# See https://learn.microsoft.com/python/api/overview/azure/identity-readme?view=azure-python#credential-classes
# credential = ManagedIdentityCredential()
namespace = "<namespace>.servicebus.windows.net"
eventhub_name = "my-eventhub"

# Producer
with EventHubProducerClient(
    fully_qualified_namespace=namespace,
    eventhub_name=eventhub_name,
    credential=credential
) as producer:
    # Use producer here (see following sections for operations)
    ...

# Consumer
with EventHubConsumerClient(
    fully_qualified_namespace=namespace,
    eventhub_name=eventhub_name,
    consumer_group="$Default",
    credential=credential
) as consumer:
    # Use consumer here (see following sections for operations)
    ...
```

## Client Types

| Client | Purpose |
|--------|---------|
| `EventHubProducerClient` | Send events to Event Hub |
| `EventHubConsumerClient` | Receive events from Event Hub |
| `BlobCheckpointStore` | Track consumer progress |

## Send Events

```python
from azure.eventhub import EventHubProducerClient, EventData
from azure.identity import DefaultAzureCredential

with EventHubProducerClient(
    fully_qualified_namespace="<namespace>.servicebus.windows.net",
    eventhub_name="my-eventhub",
    credential=DefaultAzureCredential()
) as producer:
    # Create batch (handles size limits)
    event_data_batch = producer.create_batch()

    for i in range(10):
        try:
            event_data_batch.add(EventData(f"Event {i}"))
        except ValueError:
            # Batch is full, send and create new one
            producer.send_batch(event_data_batch)
            event_data_batch = producer.create_batch()
            event_data_batch.add(EventData(f"Event {i}"))

    # Send remaining
    producer.send_batch(event_data_batch)
```

### Send to Specific Partition

```python
# By partition ID
event_data_batch = producer.create_batch(partition_id="0")

# By partition key (consistent hashing)
event_data_batch = producer.create_batch(partition_key="user-123")
```

## Receive Events

### Simple Receive

```python
from azure.eventhub import EventHubConsumerClient

def on_event(partition_context, event):
    print(f"Partition: {partition_context.partition_id}")
    print(f"Data: {event.body_as_str()}")
    partition_context.update_checkpoint(event)

with EventHubConsumerClient(
    fully_qualified_namespace="<namespace>.servicebus.windows.net",
    eventhub_name="my-eventhub",
    consumer_group="$Default",
    credential=DefaultAzureCredential()
) as consumer:
    consumer.receive(
        on_event=on_event,
        starting_position="-1",  # Beginning of stream
    )
```

### With Blob Checkpoint Store (Production)

```python
from azure.eventhub import EventHubConsumerClient
from azure.eventhub.extensions.checkpointstoreblob import BlobCheckpointStore
from azure.identity import DefaultAzureCredential

checkpoint_store = BlobCheckpointStore(
    blob_account_url="https://<account>.blob.core.windows.net",
    container_name="checkpoints",
    credential=DefaultAzureCredential()
)

with EventHubConsumerClient(
    fully_qualified_namespace="<namespace>.servicebus.windows.net",
    eventhub_name="my-eventhub",
    consumer_group="$Default",
    credential=DefaultAzureCredential(),
    checkpoint_store=checkpoint_store
) as consumer:
    def on_event(partition_context, event):
        print(f"Received: {event.body_as_str()}")
        # Checkpoint after processing
        partition_context.update_checkpoint(event)

    consumer.receive(on_event=on_event)
```

## Async Client

```python
from azure.eventhub.aio import EventHubProducerClient, EventHubConsumerClient
from azure.identity.aio import DefaultAzureCredential
import asyncio

async def send_events():
    credential = DefaultAzureCredential()

    async with EventHubProducerClient(
        fully_qualified_namespace="<namespace>.servicebus.windows.net",
        eventhub_name="my-eventhub",
        credential=credential
    ) as producer:
        batch = await producer.create_batch()
        batch.add(EventData("Async event"))
        await producer.send_batch(batch)

async def receive_events():
    async def on_event(partition_context, event):
        print(event.body_as_str())
        await partition_context.update_checkpoint(event)

    async with EventHubConsumerClient(
        fully_qualified_namespace="<namespace>.servicebus.windows.net",
        eventhub_name="my-eventhub",
        consumer_group="$Default",
        credential=DefaultAzureCredential()
    ) as consumer:
        await consumer.receive(on_event=on_event)

asyncio.run(send_events())
```

## Event Properties

```python
event = EventData("My event body")

# Set properties
event.properties = {"custom_property": "value"}
event.content_type = "application/json"

# Read properties (on receive)
print(event.body_as_str())
print(event.sequence_number)
print(event.offset)
print(event.enqueued_time)
print(event.partition_key)
```

## Get Event Hub Info

```python
with producer:
    info = producer.get_eventhub_properties()
    print(f"Name: {info['name']}")
    print(f"Partitions: {info['partition_ids']}")

    for partition_id in info['partition_ids']:
        partition_info = producer.get_partition_properties(partition_id)
        print(f"Partition {partition_id}: {partition_info['last_enqueued_sequence_number']}")
```

## Best Practices

1. **Pick sync OR async and stay consistent.** Do not mix `azure.xxx` sync clients with `azure.xxx.aio` async clients in the same call path. Choose one mode per module.
2. **Always use context managers for clients and async credentials.** Wrap every client in `with Client(...) as client:` (sync) or `async with Client(...) as client:` (async) for proper cleanup. For async `DefaultAzureCredential` from `azure.identity.aio`, also use `async with credential:` so tokens and transports are cleaned up.
3. **Use `DefaultAzureCredential`** for portable auth across local dev and Azure (avoid connection strings / API keys when possible).
4. **Use batches** for sending multiple events
5. **Use checkpoint store** in production for reliable processing
6. **Use async client** for high-throughput scenarios
7. **Use partition keys** for ordered delivery within a partition
8. **Handle batch size limits** — catch ValueError when batch is full
9. **Set appropriate consumer groups** for different applications

## Reference Files

| File | Contents |
|------|----------|
| [references/checkpointing.md](references/checkpointing.md) | Checkpoint store patterns, blob checkpointing, checkpoint strategies |
| [references/partitions.md](references/partitions.md) | Partition management, load balancing, starting positions |
| [scripts/setup_consumer.py](scripts/setup_consumer.py) | CLI for Event Hub info, consumer setup, and event sending/receiving |
