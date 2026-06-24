package com.ecommerce.orders;

import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerRecord;
import io.confluent.kafka.serializers.KafkaAvroSerializer;
import java.util.Properties;

public class OrderProducer {
    private final KafkaProducer<String, OrderEvent> producer;

    public OrderProducer() {
        Properties props = new Properties();
        props.put("bootstrap.servers", "localhost:9092");
        props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("value.serializer", "io.confluent.kafka.serializers.KafkaAvroSerializer");
        props.put("schema.registry.url", "http://localhost:8081");

        this.producer = new KafkaProducer<>(props);
    }

    public void sendOrder(OrderEvent order) {
        ProducerRecord<String, OrderEvent> record =
            new ProducerRecord<>("orders", order.getOrderId(), order);
        producer.send(record);
    }
}
