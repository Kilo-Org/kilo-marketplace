using Confluent.Kafka;
using Newtonsoft.Json;
using NotificationService.Models;

namespace NotificationService
{
    public class NotificationProducer
    {
        private readonly IProducer<string, string> _producer;

        public NotificationProducer()
        {
            var config = new ProducerConfig
            {
                BootstrapServers = "localhost:9092"
            };

            _producer = new ProducerBuilder<string, string>(config).Build();
        }

        public async Task SendNotification(UserNotification notification)
        {
            var message = new Message<string, string>
            {
                Key = notification.NotificationId,
                Value = JsonConvert.SerializeObject(notification)
            };

            await _producer.ProduceAsync("user-notifications", message);
        }

        public async Task SendSmsNotification(UserNotification notification)
        {
            var message = new Message<string, string>
            {
                Key = notification.NotificationId,
                Value = JsonConvert.SerializeObject(notification)
            };

            await _producer.ProduceAsync("sms-notifications", message);
        }
    }
}
