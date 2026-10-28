from kafka import KafkaProducer
from dataclasses import dataclass
import json

@dataclass
class AnalyticsEvent:
    event_id: str
    user_id: str
    event_type: str
    page_url: str
    ip_address: str
    timestamp: str

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def send_analytics(event: AnalyticsEvent):
    producer.send('analytics-events', value={
        'event_id': event.event_id,
        'user_id': event.user_id,
        'event_type': event.event_type,
        'page_url': event.page_url,
        'ip_address': event.ip_address,
        'timestamp': event.timestamp
    })
