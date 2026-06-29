package com.example.payment.producer;

import com.example.payment.model.PaymentEvent;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
public class PaymentProducer {

    private final KafkaTemplate<String, PaymentEvent> kafkaTemplate;

    public PaymentProducer(KafkaTemplate<String, PaymentEvent> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    public void sendPaymentEvent(PaymentEvent event) {
        kafkaTemplate.send("payment-events", event.getPaymentId(), event);
    }

    public void sendPaymentConfirmation(PaymentEvent event) {
        kafkaTemplate.send("payment-confirmations", event.getPaymentId(), event);
    }
}
