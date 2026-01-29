---
name: opentelemetry-rust
description: Expert knowledge for instrumenting Rust applications with OpenTelemetry. Use when working with Rust code instrumentation, adding observability to Rust applications, or when asked about OpenTelemetry in Rust, tracing in Rust, metrics, spans, distributed tracing, OTLP exporters, or instrumentation for Rust HTTP servers/clients, async runtime integration, databases, or any Rust application.
---

# OpenTelemetry Rust Instrumentation

Expert guidance for instrumenting Rust applications with OpenTelemetry using the official Rust SDK and manual instrumentation.

## Quick Start

### Install Dependencies

Add to your `Cargo.toml`:

```toml
[dependencies]
opentelemetry = "0.27"
opentelemetry-sdk = "0.27"
opentelemetry-otlp = "0.27"
tokio = { version = "1", features = ["full"] }
```

### Initialize OpenTelemetry

```rust
use opentelemetry::{global, KeyValue};
use opentelemetry_sdk::Resource;
use opentelemetry_sdk::trace::SdkTracerProvider;
use opentelemetry_otlp::{SpanExporter, WithExportConfig};

fn init_tracer() -> SdkTracerProvider {
    let exporter = SpanExporter::builder()
        .with_http()
        .build()
        .expect("Failed to create exporter");
    
    let provider = SdkTracerProvider::builder()
        .with_batch_exporter(exporter)
        .with_resource(Resource::builder()
            .with_service_name("my-service")
            .build())
        .build();
    
    global::set_tracer_provider(provider.clone());
    provider
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let tracer_provider = init_tracer();
    
    // Your application code here
    
    tracer_provider.shutdown()?;
    Ok(())
}
```

## Core Instrumentation Patterns

### Creating Spans

```rust
use opentelemetry::{
    global,
    trace::{TraceContextExt, Tracer},
    KeyValue,
};

fn process_request(user_id: &str) -> Result<(), Box<dyn std::error::Error>> {
    let tracer = global::tracer("my-service");
    
    tracer.in_span("process-request", |cx| {
        let span = cx.span();
        span.set_attribute(KeyValue::new("user.id", user_id.to_string()));
        
        // Do work
        match do_work() {
            Ok(_) => {
                span.set_attribute(KeyValue::new("result", "success"));
                Ok(())
            }
            Err(e) => {
                span.record_error(&e);
                Err(e)
            }
        }
    })
}
```

### Manual Span Creation and Management

```rust
use opentelemetry::trace::{Span, Status, Tracer};

fn manual_span_example() {
    let tracer = global::tracer("my-service");
    let mut span = tracer.start("manual-span");
    
    span.set_attribute(KeyValue::new("custom.attribute", "value"));
    
    // Do work
    
    span.set_status(Status::Ok);
    span.end();
}
```

### Context Propagation

```rust
use opentelemetry::Context;

fn parent_operation() {
    let tracer = global::tracer("my-service");
    
    tracer.in_span("parent", |parent_cx| {
        // Context automatically propagates to child
        child_operation(parent_cx);
    });
}

fn child_operation(cx: &Context) {
    let tracer = global::tracer("my-service");
    let _child_span = tracer.start_with_context("child", cx);
    
    // Do work
}
```

## HTTP Instrumentation

### HTTP Server (with Axum)

```rust
use axum::{Router, routing::get};
use tower_http::trace::TraceLayer;

async fn handler() -> &'static str {
    "Hello, World!"
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/", get(handler))
        .layer(TraceLayer::new_for_http());
    
    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000")
        .await
        .unwrap();
    axum::serve(listener, app).await.unwrap();
}
```

### HTTP Client (with reqwest)

For HTTP clients, you'll need to manually propagate context:

```rust
use opentelemetry::global;
use opentelemetry::trace::{TraceContextExt, Tracer};
use opentelemetry_http::HeaderInjector;
use reqwest::Client;

async fn make_request(url: &str) -> Result<String, Box<dyn std::error::Error>> {
    let tracer = global::tracer("my-service");
    
    tracer.in_span("http-request", |cx| async move {
        let mut headers = reqwest::header::HeaderMap::new();
        
        // Inject trace context into headers
        let propagator = global::get_text_map_propagator(|propagator| {
            propagator.inject_context(&cx, &mut HeaderInjector(&mut headers));
        });
        
        let client = Client::new();
        let response = client.get(url)
            .headers(headers)
            .send()
            .await?;
        
        response.text().await
    }).await
}
```

## Integration with Tracing Crate

The `tracing` crate is the recommended approach for logging and structured diagnostics in Rust. OpenTelemetry integrates seamlessly with it:

### Setup with Tracing

```toml
[dependencies]
tracing = "0.1"
tracing-subscriber = "0.3"
opentelemetry-appender-tracing = "0.27"
```

```rust
use opentelemetry_appender_tracing::layer::OpenTelemetryTracingBridge;
use opentelemetry_sdk::logs::SdkLoggerProvider;
use tracing_subscriber::prelude::*;
use tracing::{info, error};

fn init_logs() -> SdkLoggerProvider {
    let exporter = opentelemetry_otlp::LogExporter::builder()
        .with_http()
        .build()
        .expect("Failed to create log exporter");
    
    let provider = SdkLoggerProvider::builder()
        .with_batch_exporter(exporter)
        .with_resource(Resource::builder()
            .with_service_name("my-service")
            .build())
        .build();
    
    let layer = OpenTelemetryTracingBridge::new(&provider);
    tracing_subscriber::registry().with(layer).init();
    
    provider
}

fn main() {
    let logger_provider = init_logs();
    
    info!("Application started");
    error!(error.kind = "database", "Connection failed");
    
    logger_provider.shutdown().expect("Failed to shutdown logger");
}
```

## Metrics

### Creating Metrics

```rust
use opentelemetry::{global, KeyValue};
use opentelemetry::metrics::Counter;

fn setup_metrics() {
    let meter = global::meter("my-service");
    
    // Counter
    let counter = meter
        .u64_counter("http.requests")
        .with_description("Total HTTP requests")
        .build();
    
    counter.add(1, &[
        KeyValue::new("http.method", "GET"),
        KeyValue::new("http.status", 200),
    ]);
    
    // Histogram
    let histogram = meter
        .f64_histogram("http.request.duration")
        .with_unit("ms")
        .with_description("HTTP request duration")
        .build();
    
    histogram.record(150.5, &[
        KeyValue::new("http.method", "GET"),
    ]);
    
    // UpDownCounter
    let active_connections = meter
        .i64_up_down_counter("http.active_connections")
        .with_description("Number of active connections")
        .build();
    
    active_connections.add(1, &[]);  // Connection opened
    active_connections.add(-1, &[]); // Connection closed
}
```

### Async/Observable Metrics

```rust
use opentelemetry::metrics::ObservableGauge;
use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};

fn setup_async_metrics() {
    let meter = global::meter("my-service");
    let memory_usage = Arc::new(AtomicU64::new(0));
    let memory_usage_clone = memory_usage.clone();
    
    let _gauge = meter
        .u64_observable_gauge("process.memory.usage")
        .with_description("Current memory usage")
        .with_unit("bytes")
        .with_callback(move |observer| {
            let value = memory_usage_clone.load(Ordering::Relaxed);
            observer.observe(value, &[]);
        })
        .build();
}
```

## Complete Initialization

### Initializing All Signals

```rust
use opentelemetry::{global, KeyValue};
use opentelemetry_sdk::{
    logs::SdkLoggerProvider,
    metrics::SdkMeterProvider,
    trace::SdkTracerProvider,
    Resource,
};
use opentelemetry_otlp::{LogExporter, MetricExporter, SpanExporter, WithExportConfig};
use std::sync::OnceLock;

fn get_resource() -> Resource {
    static RESOURCE: OnceLock<Resource> = OnceLock::new();
    RESOURCE
        .get_or_init(|| {
            Resource::builder()
                .with_service_name("my-service")
                .with_service_version("1.0.0")
                .build()
        })
        .clone()
}

fn init_traces() -> SdkTracerProvider {
    let exporter = SpanExporter::builder()
        .with_http()
        .build()
        .expect("Failed to create trace exporter");
    
    SdkTracerProvider::builder()
        .with_batch_exporter(exporter)
        .with_resource(get_resource())
        .build()
}

fn init_metrics() -> SdkMeterProvider {
    let exporter = MetricExporter::builder()
        .with_http()
        .build()
        .expect("Failed to create metric exporter");
    
    SdkMeterProvider::builder()
        .with_periodic_exporter(exporter)
        .with_resource(get_resource())
        .build()
}

fn init_logs() -> SdkLoggerProvider {
    let exporter = LogExporter::builder()
        .with_http()
        .build()
        .expect("Failed to create log exporter");
    
    SdkLoggerProvider::builder()
        .with_batch_exporter(exporter)
        .with_resource(get_resource())
        .build()
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let tracer_provider = init_traces();
    global::set_tracer_provider(tracer_provider.clone());
    
    let meter_provider = init_metrics();
    global::set_meter_provider(meter_provider.clone());
    
    let logger_provider = init_logs();
    
    // Your application code here
    
    // Shutdown all providers
    tracer_provider.shutdown()?;
    meter_provider.shutdown()?;
    logger_provider.shutdown()?;
    
    Ok(())
}
```

## Sampling

### Probability Sampler

```rust
use opentelemetry_sdk::trace::{Sampler, SamplerResult};

let provider = SdkTracerProvider::builder()
    .with_sampler(Sampler::TraceIdRatioBased(0.1)) // Sample 10%
    .with_batch_exporter(exporter)
    .with_resource(get_resource())
    .build();
```

### Parent-Based Sampler

```rust
let provider = SdkTracerProvider::builder()
    .with_sampler(Sampler::ParentBased(Box::new(
        Sampler::TraceIdRatioBased(0.1)
    )))
    .with_batch_exporter(exporter)
    .with_resource(get_resource())
    .build();
```

## Async Runtime Integration

OpenTelemetry Rust works seamlessly with Tokio and other async runtimes:

```rust
use tokio::task;

async fn async_operation() {
    let tracer = global::tracer("my-service");
    
    tracer.in_span("async-parent", |cx| async move {
        // Spawn async task with context
        let handle = task::spawn(async move {
            let tracer = global::tracer("my-service");
            tracer.in_span("async-child", |_cx| {
                // Do async work
            });
        });
        
        handle.await.unwrap();
    }).await;
}
```

## Best Practices

1. **Use the global providers** - Set global tracer/meter providers for easy access
2. **Always shutdown** - Call `shutdown()` on all providers before application exit
3. **Use batch exporters** - Batch exporters provide better performance than simple exporters
4. **Resource attributes** - Always set `service.name` and other identifying attributes
5. **Integrate with tracing** - Use the `tracing` crate for structured logging
6. **Context propagation** - Use `in_span` for automatic context management
7. **Error handling** - Use `span.record_error()` to capture errors
8. **Semantic conventions** - Follow OpenTelemetry semantic conventions for attribute names
9. **Lazy initialization** - Use `OnceLock` or `Lazy` for resource initialization
10. **Async-aware** - Ensure context propagation works correctly with async/await

## Advanced Topics

For detailed examples covering HTTP services, database instrumentation, microservices patterns, and complex scenarios, see [references/examples.md](references/examples.md).

## Troubleshooting

### Spans not appearing
- Verify exporter endpoint is accessible
- Check that `shutdown()` is called on tracer provider
- Ensure global tracer provider is set
- Check batch exporter timeout settings

### Context not propagating
- Use `in_span` for automatic context management
- Pass context explicitly when needed
- Verify async context propagation with `task::spawn`

### Performance issues
- Use batch exporters instead of simple exporters
- Adjust batch size and timeout settings
- Implement appropriate sampling
- Consider using `AlwaysOff` sampler for high-throughput scenarios

### Compilation errors
- Ensure compatible versions of OpenTelemetry crates
- Check minimum Rust version (1.75+)
- Verify all required features are enabled

## Key Dependencies

- `opentelemetry` - Core API
- `opentelemetry-sdk` - SDK implementation
- `opentelemetry-otlp` - OTLP exporter (HTTP and gRPC)
- `opentelemetry-stdout` - Stdout exporter for development
- `opentelemetry-appender-tracing` - Integration with tracing crate
- `opentelemetry-semantic-conventions` - Semantic conventions
- `opentelemetry-http` - HTTP utilities for propagation

## Framework Integrations

- **Axum**: Use `tower-http` with `TraceLayer`
- **Actix-web**: Community instrumentation available
- **Rocket**: Manual instrumentation recommended
- **Tonic** (gRPC): Interceptor-based instrumentation

## Resources

- [OpenTelemetry Rust Docs](https://docs.rs/opentelemetry/latest/opentelemetry/)
- [OpenTelemetry Rust GitHub](https://github.com/open-telemetry/opentelemetry-rust)
- [OpenTelemetry Rust Examples](https://github.com/open-telemetry/opentelemetry-rust/tree/main/examples)
- [Tracing Crate](https://docs.rs/tracing/latest/tracing/)
