from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from models import OrderCreated, OrderUpdated
import json

# This is the problem - auto registration enabled!
producer_config = {
    'bootstrap.servers': 'localhost:9092',
    'schema.registry.url': 'http://localhost:8081',
    'auto.register.schemas': True,  # BAD PRACTICE
    'use.latest.version': False
}

schema_registry_client = SchemaRegistryClient({
    'url': producer_config['schema.registry.url']
})

def dict_to_order_created(obj, ctx):
    return obj.dict()

avro_serializer = AvroSerializer(
    schema_registry_client,
    schema_str=None,  # Will auto-register
    to_dict=dict_to_order_created
)

producer = SerializingProducer({
    **producer_config,
    'value.serializer': avro_serializer
})

def send_order_created(order: OrderCreated):
    producer.produce(
        topic='order-events',
        key=order.order_id,
        value=order
    )
    producer.flush()

def send_order_updated(order: OrderUpdated):
    producer.produce(
        topic='order-updates',
        key=order.order_id,
        value=order
    )
    producer.flush()
