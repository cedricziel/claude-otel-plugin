# OpenTelemetry Go Instrumentation Guide

## Overview

OpenTelemetry Go provides comprehensive observability for Go applications through traces, metrics, and logs. This guide covers manual instrumentation and best practices.

## Installation

Add OpenTelemetry dependencies to your Go project:

```bash
go get go.opentelemetry.io/otel \
  go.opentelemetry.io/otel/sdk \
  go.opentelemetry.io/otel/exporters/otlp/otlptrace \
  go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc \
  go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc \
  go.opentelemetry.io/otel/sdk/metric \
  go.opentelemetry.io/otel/sdk/trace \
  go.opentelemetry.io/otel/sdk/resource \
  go.opentelemetry.io/otel/semconv/v1.21.0
```

## Initialize OpenTelemetry SDK

Create a setup function to initialize the OpenTelemetry SDK:

```go
package main

import (
    "context"
    "log"
    "time"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    "go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc"
    "go.opentelemetry.io/otel/propagation"
    "go.opentelemetry.io/otel/sdk/metric"
    "go.opentelemetry.io/otel/sdk/resource"
    "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
)

func initTracer(ctx context.Context) (*trace.TracerProvider, error) {
    // Create resource with service information
    res, err := resource.New(ctx,
        resource.WithAttributes(
            semconv.ServiceName("my-service"),
            semconv.ServiceVersion("1.0.0"),
            semconv.DeploymentEnvironment("production"),
        ),
    )
    if err != nil {
        return nil, err
    }

    // Create OTLP trace exporter
    traceExporter, err := otlptracegrpc.New(ctx,
        otlptracegrpc.WithEndpoint("localhost:4317"),
        otlptracegrpc.WithInsecure(),
    )
    if err != nil {
        return nil, err
    }

    // Create tracer provider
    tp := trace.NewTracerProvider(
        trace.WithBatcher(traceExporter),
        trace.WithResource(res),
        trace.WithSampler(trace.AlwaysSample()), // Use appropriate sampler
    )

    // Set global tracer provider
    otel.SetTracerProvider(tp)

    // Set global propagator for context propagation
    otel.SetTextMapPropagator(
        propagation.NewCompositeTextMapPropagator(
            propagation.TraceContext{},
            propagation.Baggage{},
        ),
    )

    return tp, nil
}

func initMeter(ctx context.Context) (*metric.MeterProvider, error) {
    // Create resource
    res, err := resource.New(ctx,
        resource.WithAttributes(
            semconv.ServiceName("my-service"),
            semconv.ServiceVersion("1.0.0"),
        ),
    )
    if err != nil {
        return nil, err
    }

    // Create OTLP metric exporter
    metricExporter, err := otlpmetricgrpc.New(ctx,
        otlpmetricgrpc.WithEndpoint("localhost:4317"),
        otlpmetricgrpc.WithInsecure(),
    )
    if err != nil {
        return nil, err
    }

    // Create meter provider
    mp := metric.NewMeterProvider(
        metric.WithReader(
            metric.NewPeriodicReader(metricExporter,
                metric.WithInterval(10*time.Second),
            ),
        ),
        metric.WithResource(res),
    )

    // Set global meter provider
    otel.SetMeterProvider(mp)

    return mp, nil
}

func main() {
    ctx := context.Background()

    // Initialize tracer
    tp, err := initTracer(ctx)
    if err != nil {
        log.Fatal(err)
    }
    defer func() {
        if err := tp.Shutdown(ctx); err != nil {
            log.Printf("Error shutting down tracer provider: %v", err)
        }
    }()

    // Initialize meter
    mp, err := initMeter(ctx)
    if err != nil {
        log.Fatal(err)
    }
    defer func() {
        if err := mp.Shutdown(ctx); err != nil {
            log.Printf("Error shutting down meter provider: %v", err)
        }
    }()

    // Your application code here
}
```

## Creating Traces

### Basic Span Creation

```go
package main

import (
    "context"
    "log"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/codes"
    "go.opentelemetry.io/otel/trace"
)

var tracer = otel.Tracer("my-service")

func doWork(ctx context.Context, userID string) error {
    // Create a new span
    ctx, span := tracer.Start(ctx, "doWork")
    defer span.End()

    // Add attributes
    span.SetAttributes(
        attribute.String("user.id", userID),
        attribute.String("operation", "processing"),
    )

    // Add an event
    span.AddEvent("Processing started")

    // Do actual work
    if err := processData(ctx, userID); err != nil {
        // Record error
        span.SetStatus(codes.Error, "Processing failed")
        span.RecordError(err)
        return err
    }

    span.AddEvent("Processing completed")
    span.SetStatus(codes.Ok, "Success")

    return nil
}

func processData(ctx context.Context, userID string) error {
    // Child span automatically created with parent context
    ctx, span := tracer.Start(ctx, "processData")
    defer span.End()

    span.SetAttributes(attribute.String("user.id", userID))

    // Processing logic here
    // ...

    return nil
}
```

### Span Options

```go
import (
    "go.opentelemetry.io/otel/trace"
)

func createSpanWithOptions(ctx context.Context) {
    ctx, span := tracer.Start(ctx, "operation",
        trace.WithSpanKind(trace.SpanKindClient),
        trace.WithAttributes(
            attribute.String("db.system", "postgresql"),
            attribute.String("db.name", "mydb"),
        ),
    )
    defer span.End()

    // Work here
}
```

## HTTP Instrumentation

### HTTP Server

Use the `otelhttp` package for automatic HTTP server instrumentation:

```go
package main

import (
    "net/http"

    "go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
)

func main() {
    // Wrap your handler with otelhttp
    handler := http.HandlerFunc(handleRequest)
    wrappedHandler := otelhttp.NewHandler(handler, "my-service")

    http.Handle("/api/endpoint", wrappedHandler)
    http.ListenAndServe(":8080", nil)
}

func handleRequest(w http.ResponseWriter, r *http.Request) {
    // Context is automatically propagated
    ctx := r.Context()
    
    // Get current span if needed
    span := trace.SpanFromContext(ctx)
    span.SetAttributes(attribute.String("custom.attribute", "value"))

    // Your handler logic
    w.WriteHeader(http.StatusOK)
    w.Write([]byte("Hello, World!"))
}
```

### HTTP Server with Custom Handler

```go
import (
    "net/http"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/propagation"
    "go.opentelemetry.io/otel/trace"
)

var tracer = otel.Tracer("my-service")

func instrumentedHandler(w http.ResponseWriter, r *http.Request) {
    // Extract context from incoming request
    ctx := otel.GetTextMapPropagator().Extract(
        r.Context(),
        propagation.HeaderCarrier(r.Header),
    )

    // Start span
    ctx, span := tracer.Start(ctx, r.Method+" "+r.URL.Path,
        trace.WithSpanKind(trace.SpanKindServer),
        trace.WithAttributes(
            attribute.String("http.method", r.Method),
            attribute.String("http.url", r.URL.String()),
            attribute.String("http.target", r.URL.Path),
        ),
    )
    defer span.End()

    // Process request
    processRequest(ctx)

    // Set response status
    span.SetAttributes(attribute.Int("http.status_code", http.StatusOK))
    w.WriteHeader(http.StatusOK)
}
```

### HTTP Client

```go
package main

import (
    "context"
    "net/http"

    "go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
)

func makeHTTPRequest(ctx context.Context, url string) error {
    // Create HTTP client with OpenTelemetry transport
    client := &http.Client{
        Transport: otelhttp.NewTransport(http.DefaultTransport),
    }

    // Create request with context
    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    if err != nil {
        return err
    }

    // Make request (context is automatically propagated)
    resp, err := client.Do(req)
    if err != nil {
        return err
    }
    defer resp.Body.Close()

    // Process response
    return nil
}
```

### Manual HTTP Client Instrumentation

```go
import (
    "context"
    "net/http"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/propagation"
    "go.opentelemetry.io/otel/trace"
)

func callExternalAPI(ctx context.Context, url string) error {
    // Start client span
    ctx, span := tracer.Start(ctx, "GET "+url,
        trace.WithSpanKind(trace.SpanKindClient),
        trace.WithAttributes(
            attribute.String("http.method", "GET"),
            attribute.String("http.url", url),
        ),
    )
    defer span.End()

    // Create HTTP request
    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    if err != nil {
        span.RecordError(err)
        return err
    }

    // Inject trace context into request headers
    otel.GetTextMapPropagator().Inject(ctx, propagation.HeaderCarrier(req.Header))

    // Make request
    client := &http.Client{}
    resp, err := client.Do(req)
    if err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, "HTTP request failed")
        return err
    }
    defer resp.Body.Close()

    span.SetAttributes(attribute.Int("http.status_code", resp.StatusCode))

    if resp.StatusCode >= 400 {
        span.SetStatus(codes.Error, "HTTP error response")
    }

    return nil
}
```

## gRPC Instrumentation

### gRPC Server

```go
package main

import (
    "context"
    "net"

    "google.golang.org/grpc"
    "go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc"
)

func startGRPCServer() error {
    lis, err := net.Listen("tcp", ":50051")
    if err != nil {
        return err
    }

    // Create gRPC server with OpenTelemetry interceptors
    server := grpc.NewServer(
        grpc.UnaryInterceptor(otelgrpc.UnaryServerInterceptor()),
        grpc.StreamInterceptor(otelgrpc.StreamServerInterceptor()),
    )

    // Register your services
    // pb.RegisterYourServiceServer(server, &yourServiceImpl{})

    return server.Serve(lis)
}
```

### gRPC Client

```go
import (
    "context"

    "google.golang.org/grpc"
    "go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc"
)

func createGRPCClient(ctx context.Context) (*grpc.ClientConn, error) {
    // Create connection with OpenTelemetry interceptors
    conn, err := grpc.DialContext(ctx, "localhost:50051",
        grpc.WithInsecure(),
        grpc.WithUnaryInterceptor(otelgrpc.UnaryClientInterceptor()),
        grpc.WithStreamInterceptor(otelgrpc.StreamClientInterceptor()),
    )
    if err != nil {
        return nil, err
    }

    return conn, nil
}
```

## Recording Metrics

### Counter

```go
package main

import (
    "context"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/metric"
)

var (
    meter           = otel.Meter("my-service")
    requestCounter  metric.Int64Counter
)

func init() {
    var err error
    requestCounter, err = meter.Int64Counter(
        "http.server.requests",
        metric.WithDescription("Total number of HTTP requests"),
        metric.WithUnit("{request}"),
    )
    if err != nil {
        panic(err)
    }
}

func recordRequest(ctx context.Context, method, path string, statusCode int) {
    requestCounter.Add(ctx, 1,
        metric.WithAttributes(
            attribute.String("http.method", method),
            attribute.String("http.route", path),
            attribute.Int("http.status_code", statusCode),
        ),
    )
}
```

### Histogram

```go
import (
    "context"
    "time"

    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/metric"
)

var requestDuration metric.Float64Histogram

func init() {
    var err error
    requestDuration, err = meter.Float64Histogram(
        "http.server.duration",
        metric.WithDescription("HTTP request duration"),
        metric.WithUnit("ms"),
    )
    if err != nil {
        panic(err)
    }
}

func handleRequestWithMetrics(ctx context.Context, method, path string) {
    start := time.Now()
    
    // Process request
    // ...
    
    duration := float64(time.Since(start).Milliseconds())
    requestDuration.Record(ctx, duration,
        metric.WithAttributes(
            attribute.String("http.method", method),
            attribute.String("http.route", path),
        ),
    )
}
```

### Gauge (Async Instrument)

```go
import (
    "context"
    "runtime"

    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/metric"
)

func registerMemoryMetrics() error {
    _, err := meter.Int64ObservableGauge(
        "process.runtime.go.mem.heap_alloc",
        metric.WithDescription("Bytes of allocated heap objects"),
        metric.WithUnit("By"),
        metric.WithInt64Callback(func(ctx context.Context, o metric.Int64Observer) error {
            var m runtime.MemStats
            runtime.ReadMemStats(&m)
            o.Observe(int64(m.HeapAlloc))
            return nil
        }),
    )
    return err
}
```

## Database Instrumentation

### SQL Database with Manual Instrumentation

```go
package main

import (
    "context"
    "database/sql"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/codes"
    "go.opentelemetry.io/otel/trace"
)

var tracer = otel.Tracer("my-service")

type UserRepository struct {
    db *sql.DB
}

func (r *UserRepository) FindByID(ctx context.Context, userID string) (*User, error) {
    ctx, span := tracer.Start(ctx, "SELECT users",
        trace.WithSpanKind(trace.SpanKindClient),
        trace.WithAttributes(
            attribute.String("db.system", "postgresql"),
            attribute.String("db.name", "myapp"),
            attribute.String("db.operation", "SELECT"),
            attribute.String("db.sql.table", "users"),
        ),
    )
    defer span.End()

    query := "SELECT id, name, email FROM users WHERE id = $1"
    span.SetAttributes(attribute.String("db.statement", query))

    var user User
    err := r.db.QueryRowContext(ctx, query, userID).Scan(
        &user.ID,
        &user.Name,
        &user.Email,
    )

    if err != nil {
        if err == sql.ErrNoRows {
            span.SetStatus(codes.Error, "User not found")
        } else {
            span.RecordError(err)
            span.SetStatus(codes.Error, "Query failed")
        }
        return nil, err
    }

    return &user, nil
}

type User struct {
    ID    string
    Name  string
    Email string
}
```

## Context Propagation

### Goroutines

When starting goroutines, always pass the context:

```go
func processAsync(ctx context.Context, data string) {
    // Create span in main goroutine
    ctx, span := tracer.Start(ctx, "processAsync")
    defer span.End()

    // Start goroutine with context
    go func(ctx context.Context) {
        // Create child span in goroutine
        _, childSpan := tracer.Start(ctx, "async-work")
        defer childSpan.End()

        // Do async work
        performWork(data)
    }(ctx)
}
```

### Extracting and Injecting Context

```go
import (
    "context"
    "net/http"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/propagation"
)

// Extract context from HTTP headers
func extractContext(r *http.Request) context.Context {
    return otel.GetTextMapPropagator().Extract(
        r.Context(),
        propagation.HeaderCarrier(r.Header),
    )
}

// Inject context into HTTP headers
func injectContext(ctx context.Context, req *http.Request) {
    otel.GetTextMapPropagator().Inject(
        ctx,
        propagation.HeaderCarrier(req.Header),
    )
}
```

## Best Practices

1. **Always pass context**: Pass `context.Context` through your call chain to maintain trace relationships
2. **Defer span.End()**: Always defer `span.End()` immediately after starting a span
3. **Use semantic conventions**: Follow OpenTelemetry semantic conventions for attribute names
4. **Record errors properly**: Use `span.RecordError()` and `span.SetStatus()` for error handling
5. **Low cardinality**: Keep span names and attribute values low cardinality (avoid user IDs, request IDs in names)
6. **Resource attributes**: Set service name, version, and environment in resource attributes
7. **Sampling**: Use appropriate sampling strategy for production (e.g., parent-based with 10% ratio)
8. **Shutdown**: Always call `Shutdown()` on providers when application exits
9. **Metric naming**: Follow metric naming conventions (e.g., `http.server.duration`, not `httpDuration`)
10. **Context in goroutines**: Always pass context to goroutines to maintain trace propagation

## Common Patterns

### Error Handling

```go
func handleError(ctx context.Context, err error) {
    span := trace.SpanFromContext(ctx)
    if err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, err.Error())
    }
}
```

### Middleware Pattern

```go
func TracingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        ctx := r.Context()
        ctx, span := tracer.Start(ctx, r.Method+" "+r.URL.Path)
        defer span.End()

        // Create new request with updated context
        r = r.WithContext(ctx)

        // Call next handler
        next.ServeHTTP(w, r)
    })
}
```

## Environment Variables

Configure OpenTelemetry via environment variables:

```bash
export OTEL_SERVICE_NAME=my-service
export OTEL_RESOURCE_ATTRIBUTES=deployment.environment=production,service.version=1.0.0
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_EXPORTER_OTLP_HEADERS=api-key=your-key
export OTEL_TRACES_SAMPLER=parentbased_traceidratio
export OTEL_TRACES_SAMPLER_ARG=0.1
```

## Troubleshooting

### Enable Debug Logging

Use the standard `log` package or structured logging:

```go
import (
    "log"
    "os"

    "go.opentelemetry.io/otel"
)

func init() {
    // Set error handler for debugging
    otel.SetErrorHandler(otel.ErrorHandlerFunc(func(err error) {
        log.Printf("OpenTelemetry error: %v\n", err)
    }))
}
```

### Verify Spans Are Being Exported

Add a stdout exporter for debugging:

```go
import (
    "go.opentelemetry.io/otel/exporters/stdout/stdouttrace"
    "go.opentelemetry.io/otel/sdk/trace"
)

func initDebugTracer(ctx context.Context) (*trace.TracerProvider, error) {
    exporter, err := stdouttrace.New(
        stdouttrace.WithPrettyPrint(),
    )
    if err != nil {
        return nil, err
    }

    tp := trace.NewTracerProvider(
        trace.WithBatcher(exporter),
    )
    otel.SetTracerProvider(tp)

    return tp, nil
}
```
