from kafka import KafkaProducer
import json

# Legacy approach - custom JSON serialization without Schema Registry
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def publish_user_event(user_id, action, metadata):
    """
    This is the old way - just dumping JSON to bytes
    No schema validation, no registry, nothing!
    """
    event = {
        'user_id': user_id,
        'action': action,
        'timestamp': metadata.get('timestamp'),
        'ip_address': metadata.get('ip'),
        'session_id': metadata.get('session')
    }

    producer.send('user-events', value=event)
    producer.flush()

def publish_product_event(product_id, event_type, data):
    """
    Another custom serializer - inline json.dumps
    """
    event_data = {
        'product_id': product_id,
        'event_type': event_type,
        'price': data.get('price'),
        'inventory': data.get('inventory'),
        'updated_at': data.get('updated_at')
    }

    # Direct json.dumps before sending
    producer.send(
        'product-events',
        value=json.dumps(event_data).encode('utf-8')
    )
