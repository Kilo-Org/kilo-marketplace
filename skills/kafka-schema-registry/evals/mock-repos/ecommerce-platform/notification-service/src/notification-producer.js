const { Kafka } = require('kafkajs');

const kafka = new Kafka({
  clientId: 'notification-service',
  brokers: ['localhost:9092']
});

const producer = kafka.producer();

async function sendNotification(notification) {
  await producer.connect();

  await producer.send({
    topic: 'notifications',
    messages: [
      {
        key: notification.notificationId,
        value: JSON.stringify({
          notification_id: notification.notificationId,
          user_email: notification.userEmail,
          user_phone: notification.userPhone,
          message: notification.message,
          sent_at: notification.sentAt
        })
      }
    ]
  });
}

module.exports = { sendNotification };
