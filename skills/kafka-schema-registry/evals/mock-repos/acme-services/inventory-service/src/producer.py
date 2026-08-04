from confluent_kafka import Producer
import json

producer = Producer({'bootstrap.servers': 'localhost:9092'})

def send_inventory_update(product_id, quantity):
    event = {
        'product_id': product_id,
        'quantity': quantity,
        'warehouse': 'main'
    }
    producer.produce('inventory-updates', json.dumps(event).encode())
