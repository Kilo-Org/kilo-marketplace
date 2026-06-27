package com.example.streams;

import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.kstream.KStream;
import io.confluent.kafka.serializers.KafkaAvroSerializer;
import io.confluent.kafka.serializers.KafkaAvroDeserializer;

import java.util.Properties;

public class StreamsApp {

    public static void main(String[] args) {
        Properties props = new Properties();
        props.put(StreamsConfig.APPLICATION_ID_CONFIG, "streams-processor");
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");

        // Currently using payload-based schema ID (default)
        props.put("schema.registry.url", "http://localhost:8081");
        props.put("value.serializer", KafkaAvroSerializer.class.getName());
        props.put("value.deserializer", KafkaAvroDeserializer.class.getName());

        StreamsBuilder builder = new StreamsBuilder();

        KStream<String, Object> inputStream = builder.stream("input-topic");

        inputStream
            .filter((key, value) -> value != null)
            .to("output-topic");

        KafkaStreams streams = new KafkaStreams(builder.build(), props);
        streams.start();
    }
}
