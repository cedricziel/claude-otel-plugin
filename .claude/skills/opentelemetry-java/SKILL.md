---
name: opentelemetry-java
description: Expert knowledge for instrumenting Java applications with OpenTelemetry. Use when working with Java code instrumentation, adding observability to Java applications, Spring Boot applications, or when asked about OpenTelemetry in Java, tracing in Java, metrics, spans, distributed tracing, Java agent, OTLP exporters, or instrumentation libraries for Java, Spring, Hibernate, JDBC, HTTP clients/servers, or any Java framework.
---

# OpenTelemetry Java Instrumentation

Expert guidance for instrumenting Java applications with OpenTelemetry using automatic and manual instrumentation approaches.

## Quick Start

### Automatic Instrumentation (Java Agent)

Download the Java agent:
```bash
wget https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/latest/download/opentelemetry-javaagent.jar
```

Run your application:
```bash
java -javaagent:path/to/opentelemetry-javaagent.jar \
     -Dotel.service.name=your-service-name \
     -Dotel.traces.exporter=otlp \
     -Dotel.metrics.exporter=otlp \
     -Dotel.exporter.otlp.endpoint=http://localhost:4317 \
     -jar your-application.jar
```

### Key Configuration Properties

- `otel.service.name`: Service name (required)
- `otel.resource.attributes`: Additional attributes (e.g., `deployment.environment=production`)
- `otel.traces.exporter`: Trace exporter (otlp, jaeger, zipkin, logging)
- `otel.metrics.exporter`: Metrics exporter (otlp, prometheus, logging)
- `otel.exporter.otlp.endpoint`: OTLP collector endpoint
- `otel.exporter.otlp.headers`: Authentication headers

## Manual Instrumentation

### Maven Dependencies

```xml
<dependencies>
    <dependency>
        <groupId>io.opentelemetry</groupId>
        <artifactId>opentelemetry-api</artifactId>
        <version>1.33.0</version>
    </dependency>
    <dependency>
        <groupId>io.opentelemetry</groupId>
        <artifactId>opentelemetry-sdk</artifactId>
        <version>1.33.0</version>
    </dependency>
    <dependency>
        <groupId>io.opentelemetry</groupId>
        <artifactId>opentelemetry-exporter-otlp</artifactId>
        <version>1.33.0</version>
    </dependency>
</dependencies>
```

### Gradle Dependencies

```gradle
dependencies {
    implementation 'io.opentelemetry:opentelemetry-api:1.33.0'
    implementation 'io.opentelemetry:opentelemetry-sdk:1.33.0'
    implementation 'io.opentelemetry:opentelemetry-exporter-otlp:1.33.0'
}
```

## Core Instrumentation Patterns

### Initialize OpenTelemetry SDK

```java
import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.BatchSpanProcessor;
import io.opentelemetry.exporter.otlp.trace.OtlpGrpcSpanExporter;

SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
    .addSpanProcessor(BatchSpanProcessor.builder(
        OtlpGrpcSpanExporter.builder()
            .setEndpoint("http://localhost:4317")
            .build()
    ).build())
    .build();

OpenTelemetry openTelemetry = OpenTelemetrySdk.builder()
    .setTracerProvider(tracerProvider)
    .buildAndRegisterGlobal();
```

### Creating Spans

```java
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.context.Scope;

Tracer tracer = openTelemetry.getTracer("my-service", "1.0.0");

Span span = tracer.spanBuilder("operation-name").startSpan();
try (Scope scope = span.makeCurrent()) {
    span.setAttribute("user.id", userId);
    
    // Your code here
    processRequest();
    
    span.setStatus(StatusCode.OK);
} catch (Exception e) {
    span.recordException(e);
    span.setStatus(StatusCode.ERROR, "Operation failed");
    throw e;
} finally {
    span.end();
}
```

### Annotations (@WithSpan)

```java
import io.opentelemetry.instrumentation.annotations.WithSpan;
import io.opentelemetry.instrumentation.annotations.SpanAttribute;

public class MyService {
    @WithSpan
    public void processOrder(@SpanAttribute("order.id") String orderId) {
        // Automatically creates a span
        // Method parameters annotated with @SpanAttribute become span attributes
    }
}
```

## Spring Boot Integration

Add dependency:
```xml
<dependency>
    <groupId>io.opentelemetry.instrumentation</groupId>
    <artifactId>opentelemetry-spring-boot-starter</artifactId>
    <version>1.32.0-alpha</version>
</dependency>
```

Configuration in `application.properties`:
```properties
otel.service.name=my-spring-app
otel.traces.exporter=otlp
otel.exporter.otlp.endpoint=http://localhost:4317
otel.metrics.exporter=otlp
```

## Metrics

### Creating Metrics

```java
import io.opentelemetry.api.metrics.LongCounter;
import io.opentelemetry.api.metrics.Meter;

Meter meter = openTelemetry.getMeter("my-service");

// Counter
LongCounter counter = meter.counterBuilder("http.requests")
    .setDescription("Total HTTP requests")
    .build();
counter.add(1, Attributes.of(
    AttributeKey.stringKey("http.method"), "GET"
));

// Histogram
DoubleHistogram histogram = meter.histogramBuilder("http.request.duration")
    .setUnit("ms")
    .build();
histogram.record(150.5, Attributes.of(
    AttributeKey.stringKey("http.method"), "GET"
));
```

## Context Propagation

### HTTP Server

```java
import io.opentelemetry.context.Context;
import io.opentelemetry.context.propagation.TextMapGetter;

TextMapGetter<HttpServletRequest> getter = new HttpServletRequestGetter();
Context extractedContext = openTelemetry.getPropagators()
    .getTextMapPropagator()
    .extract(Context.current(), request, getter);

Span span = tracer.spanBuilder("handle-request")
    .setParent(extractedContext)
    .startSpan();
```

### HTTP Client

```java
import io.opentelemetry.context.propagation.TextMapSetter;

TextMapSetter<HttpURLConnection> setter = new HttpURLConnectionSetter();
openTelemetry.getPropagators()
    .getTextMapPropagator()
    .inject(Context.current(), connection, setter);
```

## Best Practices

1. **Use automatic instrumentation** for quick setup
2. **Resource attributes** - Always set service.name and deployment.environment
3. **Span lifecycle** - Always close spans (use try-with-resources)
4. **Exception recording** - Use `span.recordException()` for errors
5. **Semantic conventions** - Follow OpenTelemetry semantic conventions
6. **Context propagation** - Use `Scope` to propagate context
7. **Batch processing** - Use `BatchSpanProcessor` for performance
8. **Sampling** - Configure appropriate sampling for production

## Advanced Topics

For detailed examples covering Spring Boot, JDBC, HTTP clients, gRPC, and advanced patterns, see [references/examples.md](references/examples.md).

## Troubleshooting

### No spans appearing
- Verify Java agent is attached (`-javaagent` flag)
- Check exporter endpoint is accessible
- Ensure spans are ended

### Spring Boot not working
- Check starter dependency version
- Verify `application.properties` configuration
- Enable debug logging: `logging.level.io.opentelemetry=DEBUG`

### Performance issues
- Use `BatchSpanProcessor` instead of `SimpleSpanProcessor`
- Adjust batch size and delay
- Implement sampling

## Key Dependencies

- `io.opentelemetry:opentelemetry-api` - Core API
- `io.opentelemetry:opentelemetry-sdk` - SDK implementation
- `io.opentelemetry:opentelemetry-exporter-otlp` - OTLP exporter
- `io.opentelemetry.instrumentation:opentelemetry-instrumentation-annotations` - Annotations
- `io.opentelemetry.instrumentation:opentelemetry-spring-boot-starter` - Spring Boot support

## Resources

- [OpenTelemetry Java Docs](https://opentelemetry.io/docs/languages/java/)
- [OpenTelemetry Java GitHub](https://github.com/open-telemetry/opentelemetry-java)
- [Java Instrumentation](https://github.com/open-telemetry/opentelemetry-java-instrumentation)
