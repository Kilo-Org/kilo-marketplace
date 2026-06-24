package com.tx.payments;

import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
public class PaymentProducer {
    private final KafkaTemplate<String, PaymentProcessedEvent> kafkaTemplate;

    public PaymentProducer(KafkaTemplate<String, PaymentProcessedEvent> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    public void sendPaymentProcessed(PaymentProcessedEvent event) {
        // Same topic as order service, different event type!
        kafkaTemplate.send("transaction-events", event.getPaymentId(), event);
    }
}
