# Production Hardening Reference

Read this file when the user's target is production. These additions transform a working Streams app into one that's ready for container orchestration, structured observability, and operational resilience.

**Reference docs:** [Kafka Streams operations guide](https://docs.confluent.io/platform/current/streams/developer-guide/running-app.md) | [Monitoring Streams apps](https://docs.confluent.io/platform/current/streams/monitoring.md)

## Table of Contents
- [Error Handling (Four-Tier Model)](#error-handling)
- [Logging: Dev vs Production](#logging)
- [Health Checks and Liveness Probes](#health-checks)
- [Dockerfile](#dockerfile)
- [Deployment Sizing](#deployment-sizing)
- [DLQ with KIP-1034](#dlq)

---

## Error Handling

Kafka Streams has four layers of error handling. Each catches a different category of failure. Production apps should configure all four.

### Layer 1: DeserializationExceptionHandler
**Catches:** Bad input records that can't be deserialized (corrupt bytes, schema mismatch, missing magic byte).

```properties
# Dev: log and skip
default.deserialization.exception.handler=org.apache.kafka.streams.errors.LogAndContinueExceptionHandler
# Prod: route to DLQ (see KIP-1034 below)
```

### Layer 2: ProcessingExceptionHandler (KIP-1034)
**Catches:** Exceptions thrown inside topology operations (map, filter, aggregate lambdas, join value joiners). New in recent KS versions.

```properties
# Dev: log and continue
processing.exception.handler=org.apache.kafka.streams.errors.LogAndContinueProcessingExceptionHandler
# Prod: route to DLQ
processing.exception.handler=org.apache.kafka.streams.errors.DeadLetterQueueExceptionHandler
```

### Layer 3: ProductionExceptionHandler
**Catches:** Failures writing to output or changelog topics (serialization errors, record too large, broker unavailable).

```java
public class SafeProductionExceptionHandler implements ProductionExceptionHandler {
    @Override
    public ProductionExceptionHandlerResponse handle(
            ErrorHandlerContext context,
            ProducerRecord<byte[], byte[]> record,
            Exception exception) {
        if (exception instanceof RecordTooLargeException) {
            return ProductionExceptionHandlerResponse.CONTINUE;  // skip oversized
        }
        return ProductionExceptionHandlerResponse.FAIL;  // fail on everything else
    }

    @Override
    public ProductionExceptionHandlerResponse handleSerializationException(
            ErrorHandlerContext context,
            ProducerRecord record,
            Exception exception) {
        // Serialization failures are usually bugs — fail fast
        return ProductionExceptionHandlerResponse.FAIL;
    }
}
```

### Layer 4: StreamsUncaughtExceptionHandler (KIP-671)
**Catches:** Anything that kills a stream thread — unhandled exceptions that escaped all other layers.

Use the MaxFailures pattern (rate-limited thread replacement):

```java
import org.apache.kafka.streams.errors.StreamsUncaughtExceptionHandler;
import org.apache.kafka.streams.errors.StreamsUncaughtExceptionHandler.StreamThreadExceptionResponse;
import java.time.Duration;
import java.time.Instant;

public class MaxFailuresUncaughtExceptionHandler implements StreamsUncaughtExceptionHandler {
    private final int maxFailures;
    private final long maxTimeIntervalMillis;
    private Instant previousErrorTime;
    private int currentFailureCount;

    public MaxFailuresUncaughtExceptionHandler(int maxFailures, long maxTimeIntervalMillis) {
        this.maxFailures = maxFailures;
        this.maxTimeIntervalMillis = maxTimeIntervalMillis;
    }

    @Override
    public StreamThreadExceptionResponse handle(Throwable throwable) {
        currentFailureCount++;
        Instant now = Instant.now();
        if (previousErrorTime == null) {
            previousErrorTime = now;
        }
        long millisBetweenFailure = Duration.between(previousErrorTime, now).toMillis();
        if (currentFailureCount >= maxFailures) {
            if (millisBetweenFailure <= maxTimeIntervalMillis) {
                return StreamThreadExceptionResponse.SHUTDOWN_APPLICATION;
            }
            currentFailureCount = 0;
            previousErrorTime = null;
        }
        previousErrorTime = now;
        // Check for unrecoverable errors
        Throwable cause = throwable;
        while (cause.getCause() != null) cause = cause.getCause();
        if (cause instanceof org.apache.kafka.common.errors.UnsupportedVersionException) {
            return StreamThreadExceptionResponse.SHUTDOWN_APPLICATION;
        }
        return StreamThreadExceptionResponse.REPLACE_THREAD;
    }
}
```

**How it works:** If N failures (default: 5) happen within M milliseconds (default: 1 minute), something is fundamentally broken — shut down the application. Otherwise, replace the failed thread and keep processing. Always shut down on `UnsupportedVersionException` (broker version mismatch).

**Summary:**

| Layer | Catches | Dev | Prod |
|-------|---------|-----|------|
| Deserialization | Bad input | LogAndContinue | DLQ |
| Processing (KIP-1034) | Lambda exceptions | LogAndContinue | DLQ |
| Production | Output failures | Default | Custom |
| Uncaught (KIP-671) | Thread failures | REPLACE_THREAD | MaxFailures |

---

## Logging

**Dev:** `slf4j-simple:2.0.16` (console, no config).
**Prod:** Replace with Logback + JSON for log aggregation:
```groovy
implementation 'ch.qos.logback:logback-classic:1.5.16'
implementation 'net.logstash.logback:logstash-logback-encoder:8.0'
```

**src/main/resources/logback.xml:**
```xml
<configuration>
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="net.logstash.logback.encoder.LogstashEncoder">
            <includeMdcKeyName>application.id</includeMdcKeyName>
            <includeMdcKeyName>thread.id</includeMdcKeyName>
        </encoder>
    </appender>

    <!-- Kafka Streams internals — WARN to reduce noise -->
    <logger name="org.apache.kafka" level="WARN"/>
    <!-- Your app logic — INFO -->
    <logger name="com.example" level="INFO"/>
    <!-- State restoration progress — useful during recovery -->
    <logger name="org.apache.kafka.streams.processor.internals.StoreChangelogReader" level="INFO"/>

    <root level="INFO">
        <appender-ref ref="STDOUT"/>
    </root>
</configuration>
```

This outputs JSON lines to stdout, which container runtimes and log collectors pick up natively. No file rotation needed — the orchestrator handles log lifecycle.

---

## Health Checks

Kafka Streams tracks its own state via `KafkaStreams.State` (CREATED, REBALANCING, RUNNING, PENDING_SHUTDOWN, PENDING_ERROR, ERROR, NOT_RUNNING). Expose this over HTTP for Kubernetes liveness and readiness probes.

Use the JDK's built-in `com.sun.net.httpserver.HttpServer` to avoid adding a web framework dependency:

```java
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;

public class HealthCheckServer {

    public static void start(KafkaStreams streams, int port) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);

        // Liveness: is the JVM healthy and Streams not in ERROR state?
        server.createContext("/health/live", exchange -> {
            KafkaStreams.State state = streams.state();
            boolean alive = state != KafkaStreams.State.ERROR
                         && state != KafkaStreams.State.NOT_RUNNING;
            int status = alive ? 200 : 503;
            String body = "{\"status\":\"" + (alive ? "UP" : "DOWN") + "\",\"state\":\"" + state + "\"}";
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(status, body.length());
            exchange.getResponseBody().write(body.getBytes());
            exchange.getResponseBody().close();
        });

        // Readiness: is Streams fully RUNNING and ready to process?
        server.createContext("/health/ready", exchange -> {
            boolean ready = streams.state() == KafkaStreams.State.RUNNING;
            int status = ready ? 200 : 503;
            String body = "{\"status\":\"" + (ready ? "UP" : "DOWN") + "\",\"state\":\"" + streams.state() + "\"}";
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(status, body.length());
            exchange.getResponseBody().write(body.getBytes());
            exchange.getResponseBody().close();
        });

        server.setExecutor(null);
        server.start();
    }
}
```

**In App.java:**
```java
KafkaStreams streams = new KafkaStreams(topology, props);
HealthCheckServer.start(streams, 8080);
streams.start();
```

**Kubernetes deployment snippet:**
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
```

The distinction matters: during a rebalance, the app is alive (don't kill it) but not ready (don't send traffic to IQ endpoints). Without separate probes, K8s will restart apps during normal rebalances — causing cascading restarts.

---

## Dockerfile

```dockerfile
FROM eclipse-temurin:17-jre-alpine

# Create non-root user
RUN addgroup -S streams && adduser -S streams -G streams

WORKDIR /app

# Copy the application fat jar (built with: ./gradlew shadowJar or ./gradlew distTar)
COPY build/libs/*-all.jar app.jar

# State directory — must match state.dir in application.properties
# Do NOT use /tmp — container runtimes may clear it on restart, losing state
RUN mkdir -p /var/kafka-streams/state && chown streams:streams /var/kafka-streams/state

USER streams

# JVM settings for containers:
# -XX:+UseG1GC: best GC for Streams workloads (mixed heap + off-heap RocksDB)
# -XX:MaxGCPauseMillis=20: keep GC pauses short to avoid session timeouts
# -XX:MaxRAMPercentage=75: leave 25% for RocksDB off-heap (block cache, memtables)
# -XX:+UseContainerSupport: respect container memory limits (default in JDK 17)
ENV JAVA_OPTS="-XX:+UseG1GC -XX:MaxGCPauseMillis=20 -XX:MaxRAMPercentage=75 -XX:+UseContainerSupport"

EXPOSE 8080

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
```

**Key point on memory:** Kafka Streams with RocksDB uses significant off-heap memory (block cache, write buffers, bloom filters). Setting `-Xmx` to the full container limit will cause OOM kills. The `MaxRAMPercentage=75` leaves headroom for RocksDB. For stateful apps with many partitions, you may need to lower this further — see `architecture.md` § Memory (stateful apps) for the canonical formula.

**build.gradle addition for fat jar** (add `shadow` plugin):
```groovy
plugins {
    id 'com.github.johnrengelman.shadow' version '8.1.1'
}
```

Then build with: `./gradlew shadowJar`

---

## Deployment Sizing

**Parallelism:** `instances × num.stream.threads ≤ input_partitions`. More = idle hot standbys.

**Stateless:** Scale horizontally. More threads/instance (match CPU), fewer instances. Constraints: CPU, network.

**Stateful:** Scale carefully. Prefer fewer large instances over many small (restoration expensive). Calculate RocksDB memory: see `architecture.md` § Memory.

### Container Resources

```yaml
resources:
  requests: { memory: "2Gi", cpu: "1000m" }  # 1 core/thread
  limits: { memory: "2Gi" }  # NO CPU limit (throttling → rebalances)
```
Memory: JVM heap (75%) + RocksDB (25%). **Never limit CPU** — throttling causes poll timeouts.

### Persistent Volumes (Critical for Stateful Apps)

Always use persistent volumes (PVCs) for stateful KS apps in K8s. Ephemeral storage forces full state restoration on every restart, which can take hours for large stores.

```yaml
volumeClaimTemplates:
- metadata:
    name: state-store
  spec:
    accessModes: ["ReadWriteOnce"]
    storageClassName: "ssd"
    resources:
      requests:
        storage: "50Gi"    # 3x expected state size (SST + WAL + compaction)
```

Mount at the `state.dir` path. Size at 3x expected state size to accommodate SST files, WAL, and compaction overhead. Monitor disk usage with alerts at 70%.

### Cloud Load Balancer Configuration

Cloud load balancers (especially Azure) drop idle TCP connections after their timeout (4-30 min). If a stream thread is busy in a long operation and doesn't send traffic, the connection is dropped.

**Fix:**
- Set OS-level TCP keepalive < cloud LB idle timeout
- Set `connections.max.idle.ms` < cloud LB idle timeout
- Fix root cause of long-running operations

### Deployment Timeout Configuration

```properties
# Critical timeouts to align for production:
consumer.max.poll.interval.ms=600000     # 10 min (match to worst-case processing time)
consumer.session.timeout.ms=45000         # 45s (heartbeat detection)
consumer.request.timeout.ms=600000        # Match max.poll.interval.ms
# For EOS: transaction.timeout.ms <= max.poll.interval.ms
```

---

## DLQ with KIP-1034

Config: `processing.exception.handler=org.apache.kafka.streams.errors.DeadLetterQueueExceptionHandler`

DLQ naming: `<application.id>-<source-topic>-dlq`. Headers include original topic/partition/offset, exception, timestamp.

**Pre-create DLQ topics** (production clusters have `auto.create.topics.enable=false`):
```bash
kafka-topics --create --topic my-app-input-dlq --partitions 4 --replication-factor 3 \
  --config retention.ms=604800000 --bootstrap-server <broker>
# CC: confluent kafka topic create my-app-input-dlq --partitions 4
```

| Handler | Use |
|---------|-----|
| `LogAndContinueExceptionHandler` | Dev |
| `DeadLetterQueueExceptionHandler` | Production |
| `LogAndFailExceptionHandler` | Strict correctness |
| Custom | Complex routing |
