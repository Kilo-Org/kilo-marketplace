using System;
using Newtonsoft.Json;

namespace NotificationService.Models
{
    public class UserNotification
    {
        [JsonProperty("notification_id")]
        public string NotificationId { get; set; }

        [JsonProperty("user_id")]
        public string UserId { get; set; }

        [JsonProperty("email")]
        public string Email { get; set; }

        [JsonProperty("phone_number")]
        public string PhoneNumber { get; set; }

        [JsonProperty("first_name")]
        public string FirstName { get; set; }

        [JsonProperty("last_name")]
        public string LastName { get; set; }

        [JsonProperty("home_address")]
        public string HomeAddress { get; set; }

        [JsonProperty("ssn")]
        public string SSN { get; set; }

        [JsonProperty("date_of_birth")]
        public DateTime DateOfBirth { get; set; }

        [JsonProperty("ip_address")]
        public string IPAddress { get; set; }

        [JsonProperty("message")]
        public string Message { get; set; }

        [JsonProperty("sent_at")]
        public DateTime SentAt { get; set; }
    }
}
