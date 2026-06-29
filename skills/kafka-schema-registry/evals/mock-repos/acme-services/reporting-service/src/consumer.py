from kafka import KafkaConsumer

# This service only consumes - no producer
consumer = KafkaConsumer(
    'user-events',
    'inventory-updates',
    bootstrap_servers=['localhost:9092']
)

for message in consumer:
    print(f"Received: {message.value}")
