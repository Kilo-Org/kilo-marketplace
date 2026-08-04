package main

import (
	"encoding/json"
	"log"

	"github.com/IBM/sarama"
)

type CustomerEvent struct {
	CustomerID    string  `json:"customer_id"`
	Email         string  `json:"email"`
	PhoneNumber   string  `json:"phone_number"`
	FirstName     string  `json:"first_name"`
	LastName      string  `json:"last_name"`
	AccountNumber string  `json:"account_number"`
	TotalSpent    float64 `json:"total_spent"`
}

type OrderEvent struct {
	OrderID    string  `json:"order_id"`
	CustomerID string  `json:"customer_id"`
	Amount     float64 `json:"amount"`
	Status     string  `json:"status"`
}

func main() {
	config := sarama.NewConfig()
	config.Producer.Return.Successes = true

	producer, err := sarama.NewSyncProducer([]string{"localhost:9092"}, config)
	if err != nil {
		log.Fatal(err)
	}
	defer producer.Close()

	// Custom serialization - json.Marshal before producing
	customer := CustomerEvent{
		CustomerID:    "cust-123",
		Email:         "john.doe@example.com",
		PhoneNumber:   "555-1234",
		FirstName:     "John",
		LastName:      "Doe",
		AccountNumber: "ACC-9876",
		TotalSpent:    1250.50,
	}

	// This is the problem - manual JSON marshaling without Schema Registry
	data, err := json.Marshal(customer)
	if err != nil {
		log.Fatal(err)
	}

	msg := &sarama.ProducerMessage{
		Topic: "customer-events",
		Value: sarama.ByteEncoder(data),
	}

	_, _, err = producer.SendMessage(msg)
	if err != nil {
		log.Fatal(err)
	}

	// Another event type
	order := OrderEvent{
		OrderID:    "ord-456",
		CustomerID: "cust-123",
		Amount:     99.99,
		Status:     "pending",
	}

	orderData, _ := json.Marshal(order)
	orderMsg := &sarama.ProducerMessage{
		Topic: "order-events",
		Value: sarama.ByteEncoder(orderData),
	}

	producer.SendMessage(orderMsg)
}
