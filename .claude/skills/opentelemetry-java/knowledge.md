# OpenTelemetry Java Instrumentation Guide

## Overview

OpenTelemetry Java provides comprehensive observability for Java applications through traces, metrics, and logs. This guide covers both automatic and manual instrumentation approaches.

## Automatic Instrumentation (Java Agent)

The simplest way to get started with OpenTelemetry in Java is using the automatic instrumentation agent.

### Setup

1. Download the latest OpenTelemetry Java agent:
```bash
wget https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/latest/download/opentelemetry-javaagent.jar
```

2. Run your application with the agent:
```bash
java -javaagent:path/to/opentelemetry-javaagent.jar \
     -Dotel.service.name=your-service-name \
     -Dotel.traces.exporter=otlp \
     -Dotel.metrics.exporter=otlp \
     -Dotel.logs.exporter=otlp \
     -Dotel.exporter.otlp.endpoint=http://localhost:4317 \
     -jar your-application.jar
```

### Key Configuration Properties

- `otel.service.name`: Name of your service (required)
- `otel.resource.attributes`: Additional resource attributes (e.g., `deployment.environment=production`)
- `otel.traces.exporter`: Trace exporter (otlp, jaeger, zipkin, logging, none)
- `otel.metrics.exporter`: Metrics exporter (otlp, prometheus, logging, none)
- `otel.logs.exporter`: Logs exporter (otlp, logging, none)
- `otel.exporter.otlp.endpoint`: OTLP collector endpoint
- `otel.exporter.otlp.headers`: Authentication headers (e.g., `api-key=your-key`)

## Manual Instrumentation

For more control, use manual instrumentation with the OpenTelemetry API.

### Maven Dependencies

Add these dependencies to your `pom.xml`:

```xml
<dependencies>
    <!-- OpenTelemetry API -->
    <dependency>
        <groupId>io.opentelemetry</groupId>
        <artifactId>opentelemetry-api</artifactId>
        <version>1.33.0</version>
    </dependency>
    
    <!-- OpenTelemetry SDK -->
    <dependency>
        <groupId>io.opentelemetry</groupId>
        <artifactId>opentelemetry-sdk</artifactId>
        <version>1.33.0</version>
    </dependency>
    
    <!-- OTLP Exporter -->
    <dependency>
        <groupId>io.opentelemetry</groupId>
        <artifactId>opentelemetry-exporter-otlp</artifactId>
        <version>1.33.0</version>
    </dependency>
    
    <!-- Instrumentation Annotations (optional) -->
    <dependency>
        <groupId>io.opentelemetry.instrumentation</groupId>
        <artifactId>opentelemetry-instrumentation-annotations</artifactId>
        <version>2.0.0</version>
    </dependency>
</dependencies>
```

### Gradle Dependencies

Add these to your `build.gradle`:

```gradle
dependencies {
    implementation 'io.opentelemetry:opentelemetry-api:1.33.0'
    implementation 'io.opentelemetry:opentelemetry-sdk:1.33.0'
    implementation 'io.opentelemetry:opentelemetry-exporter-otlp:1.33.0'
    implementation 'io.opentelemetry.instrumentation:opentelemetry-instrumentation-annotations:2.0.0'
}
```

### Initialize OpenTelemetry SDK

```java
import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.trace.propagation.W3CTraceContextPropagator;
import io.opentelemetry.context.propagation.ContextPropagators;
import io.opentelemetry.exporter.otlp.trace.OtlpGrpcSpanExporter;
import io.opentelemetry.exporter.otlp.metrics.OtlpGrpcMetricExporter;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.resources.Resource;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.BatchSpanProcessor;
import io.opentelemetry.sdk.metrics.SdkMeterProvider;
import io.opentelemetry.sdk.metrics.export.PeriodicMetricReader;
import io.opentelemetry.semconv.ResourceAttributes;

public class OpenTelemetryConfig {
    
    public static OpenTelemetry initOpenTelemetry() {
        // Create resource with service name
        Resource resource = Resource.getDefault()
                .merge(Resource.create(
                    Attributes.of(
                        ResourceAttributes.SERVICE_NAME, "your-service-name",
                        ResourceAttributes.SERVICE_VERSION, "1.0.0",
                        ResourceAttributes.DEPLOYMENT_ENVIRONMENT, "production"
                    )
                ));

        // Configure trace exporter
        OtlpGrpcSpanExporter spanExporter = OtlpGrpcSpanExporter.builder()
                .setEndpoint("http://localhost:4317")
                .build();

        // Configure tracer provider
        SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
                .addSpanProcessor(BatchSpanProcessor.builder(spanExporter).build())
                .setResource(resource)
                .build();

        // Configure metric exporter
        OtlpGrpcMetricExporter metricExporter = OtlpGrpcMetricExporter.builder()
                .setEndpoint("http://localhost:4317")
                .build();

        // Configure meter provider
        SdkMeterProvider meterProvider = SdkMeterProvider.builder()
                .registerMetricReader(
                    PeriodicMetricReader.builder(metricExporter).build()
                )
                .setResource(resource)
                .build();

        // Build OpenTelemetry SDK
        OpenTelemetry openTelemetry = OpenTelemetrySdk.builder()
                .setTracerProvider(tracerProvider)
                .setMeterProvider(meterProvider)
                .setPropagators(ContextPropagators.create(
                    W3CTraceContextPropagator.getInstance()
                ))
                .buildAndRegisterGlobal();

        // Add shutdown hook
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            tracerProvider.close();
            meterProvider.close();
        }));

        return openTelemetry;
    }
}
```

### Creating Spans (Traces)

#### Basic Span Creation

```java
import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.context.Scope;

public class MyService {
    private final Tracer tracer;
    
    public MyService(OpenTelemetry openTelemetry) {
        this.tracer = openTelemetry.getTracer("my-service", "1.0.0");
    }
    
    public void doWork() {
        // Create a span
        Span span = tracer.spanBuilder("doWork")
                .startSpan();
        
        try (Scope scope = span.makeCurrent()) {
            // Your business logic here
            span.setAttribute("custom.attribute", "value");
            span.addEvent("Processing started");
            
            // Actual work
            processData();
            
            span.addEvent("Processing completed");
        } catch (Exception e) {
            span.setStatus(StatusCode.ERROR, "Operation failed");
            span.recordException(e);
            throw e;
        } finally {
            span.end();
        }
    }
    
    private void processData() {
        // Nested span
        Span childSpan = tracer.spanBuilder("processData")
                .startSpan();
        
        try (Scope scope = childSpan.makeCurrent()) {
            // Processing logic
        } finally {
            childSpan.end();
        }
    }
}
```

#### Using @WithSpan Annotation

```java
import io.opentelemetry.instrumentation.annotations.WithSpan;
import io.opentelemetry.instrumentation.annotations.SpanAttribute;

public class MyService {
    
    @WithSpan
    public String processOrder(@SpanAttribute("order.id") String orderId) {
        // Method automatically wrapped in a span
        // orderId automatically added as span attribute
        return "Order processed: " + orderId;
    }
    
    @WithSpan(value = "custom-span-name", kind = SpanKind.CLIENT)
    public void callExternalService() {
        // Custom span name and kind
    }
}
```

### Recording Metrics

```java
import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.metrics.Meter;
import io.opentelemetry.api.metrics.LongCounter;
import io.opentelemetry.api.metrics.DoubleHistogram;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.common.AttributeKey;

public class MetricsExample {
    private final Meter meter;
    private final LongCounter requestCounter;
    private final DoubleHistogram requestDuration;
    
    public MetricsExample(OpenTelemetry openTelemetry) {
        this.meter = openTelemetry.getMeter("my-service", "1.0.0");
        
        // Counter for number of requests
        this.requestCounter = meter
                .counterBuilder("http.server.requests")
                .setDescription("Total number of HTTP requests")
                .setUnit("1")
                .build();
        
        // Histogram for request duration
        this.requestDuration = meter
                .histogramBuilder("http.server.duration")
                .setDescription("HTTP request duration")
                .setUnit("ms")
                .build();
    }
    
    public void handleRequest(String method, String endpoint) {
        long startTime = System.currentTimeMillis();
        
        try {
            // Process request
            doWork();
            
            // Record successful request
            Attributes attributes = Attributes.of(
                AttributeKey.stringKey("http.method"), method,
                AttributeKey.stringKey("http.route"), endpoint,
                AttributeKey.longKey("http.status_code"), 200L
            );
            
            requestCounter.add(1, attributes);
            requestDuration.record(
                System.currentTimeMillis() - startTime, 
                attributes
            );
        } catch (Exception e) {
            // Record failed request
            Attributes attributes = Attributes.of(
                AttributeKey.stringKey("http.method"), method,
                AttributeKey.stringKey("http.route"), endpoint,
                AttributeKey.longKey("http.status_code"), 500L
            );
            
            requestCounter.add(1, attributes);
            throw e;
        }
    }
    
    private void doWork() {
        // Business logic
    }
}
```

### Context Propagation

OpenTelemetry automatically propagates context in most cases, but you can also do it manually:

```java
import io.opentelemetry.context.Context;
import io.opentelemetry.context.Scope;

public class ContextExample {
    
    public void parentMethod() {
        Span parentSpan = tracer.spanBuilder("parent").startSpan();
        
        try (Scope scope = parentSpan.makeCurrent()) {
            // Current context includes parentSpan
            childMethod(); // Will automatically be a child of parentSpan
        } finally {
            parentSpan.end();
        }
    }
    
    public void childMethod() {
        // Gets current context automatically
        Span childSpan = tracer.spanBuilder("child").startSpan();
        try (Scope scope = childSpan.makeCurrent()) {
            // Work here
        } finally {
            childSpan.end();
        }
    }
    
    // Manual context passing
    public void asyncWork() {
        Context context = Context.current();
        
        executor.submit(() -> {
            try (Scope scope = context.makeCurrent()) {
                // Context is available in async thread
                Span span = tracer.spanBuilder("async-work").startSpan();
                try (Scope spanScope = span.makeCurrent()) {
                    // Work
                } finally {
                    span.end();
                }
            }
        });
    }
}
```

## Spring Boot Integration

For Spring Boot applications, use the OpenTelemetry Spring Boot starter:

### Dependencies

```xml
<dependency>
    <groupId>io.opentelemetry.instrumentation</groupId>
    <artifactId>opentelemetry-spring-boot-starter</artifactId>
    <version>2.0.0-alpha</version>
</dependency>
```

### Configuration (application.properties)

```properties
# Service name
otel.service.name=my-spring-app

# Resource attributes
otel.resource.attributes=deployment.environment=production,service.version=1.0.0

# Exporter configuration
otel.exporter.otlp.endpoint=http://localhost:4317
otel.traces.exporter=otlp
otel.metrics.exporter=otlp
otel.logs.exporter=otlp

# Sampling (optional)
otel.traces.sampler=parentbased_traceidratio
otel.traces.sampler.arg=0.1
```

## Best Practices

1. **Resource Attributes**: Always set service name and environment
2. **Span Naming**: Use meaningful, low-cardinality names (e.g., "GET /api/users" not "GET /api/users/123")
3. **Error Handling**: Always record exceptions and set error status
4. **Span Attributes**: Add relevant context but avoid high-cardinality values (like user IDs in span names)
5. **Sampling**: Use appropriate sampling strategy for production (e.g., 10% trace sampling)
6. **Metrics**: Use appropriate metric types (Counter for counts, Histogram for distributions)
7. **Context Propagation**: Ensure context is propagated across async boundaries
8. **Shutdown**: Always close providers on application shutdown

## Common Frameworks Support

OpenTelemetry Java agent automatically instruments:
- Spring Boot / Spring MVC / Spring WebFlux
- Jakarta EE / Java EE (Servlets, JAX-RS, JMS)
- JDBC / Hibernate / JPA
- Apache HttpClient / OkHttp / Netty
- Kafka / RabbitMQ
- Redis / MongoDB / Cassandra
- gRPC
- And many more...

## Troubleshooting

### Enable Debug Logging

```bash
-Dotel.javaagent.debug=true
-Dotel.traces.exporter=logging
-Dotel.metrics.exporter=logging
```

### Check Spans Are Being Created

Add logging exporter to see spans in console:

```bash
-Dotel.traces.exporter=logging,otlp
```

### Verify SDK Initialization

Check that the SDK is properly initialized and registered globally:

```java
OpenTelemetry otel = GlobalOpenTelemetry.get();
if (otel == OpenTelemetry.noop()) {
    System.err.println("OpenTelemetry not initialized!");
}
```
