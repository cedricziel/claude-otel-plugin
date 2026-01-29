# OpenTelemetry Rust Examples

> **Note**: These examples focus on key instrumentation patterns. Some imports and helper functions are abbreviated or omitted for clarity. In production code, ensure all necessary imports are included and helper functions are properly defined.

## Example 1: Complete HTTP Service with Traces and Metrics

```rust
use axum::{
    extract::State,
    http::StatusCode,
    routing::{get, post},
    Json, Router,
};
use opentelemetry::{
    global,
    trace::{TraceContextExt, Tracer},
    KeyValue,
};
use opentelemetry_sdk::{
    metrics::SdkMeterProvider,
    trace::SdkTracerProvider,
    Resource,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tower_http::trace::TraceLayer;

#[derive(Clone)]
struct AppState {
    request_counter: opentelemetry::metrics::Counter<u64>,
    request_duration: opentelemetry::metrics::Histogram<f64>,
}

#[derive(Serialize, Deserialize)]
struct User {
    id: u64,
    name: String,
    email: String,
}

fn init_telemetry() -> (SdkTracerProvider, SdkMeterProvider) {
    let resource = Resource::builder()
        .with_service_name("user-service")
        .with_service_version("1.0.0")
        .build();
    
    // Initialize tracing
    let trace_exporter = opentelemetry_otlp::SpanExporter::builder()
        .with_http()
        .build()
        .expect("Failed to create trace exporter");
    
    let tracer_provider = SdkTracerProvider::builder()
        .with_batch_exporter(trace_exporter)
        .with_resource(resource.clone())
        .build();
    
    global::set_tracer_provider(tracer_provider.clone());
    
    // Initialize metrics
    let metric_exporter = opentelemetry_otlp::MetricExporter::builder()
        .with_http()
        .build()
        .expect("Failed to create metric exporter");
    
    let meter_provider = SdkMeterProvider::builder()
        .with_periodic_exporter(metric_exporter)
        .with_resource(resource)
        .build();
    
    global::set_meter_provider(meter_provider.clone());
    
    (tracer_provider, meter_provider)
}

fn init_metrics() -> AppState {
    let meter = global::meter("user-service");
    
    let request_counter = meter
        .u64_counter("http.server.requests")
        .with_description("Total HTTP requests")
        .build();
    
    let request_duration = meter
        .f64_histogram("http.server.duration")
        .with_unit("ms")
        .with_description("HTTP request duration")
        .build();
    
    AppState {
        request_counter,
        request_duration,
    }
}

async fn get_user(
    State(state): State<Arc<AppState>>,
    axum::extract::Path(user_id): axum::extract::Path<u64>,
) -> Result<Json<User>, StatusCode> {
    let tracer = global::tracer("user-service");
    
    tracer.in_span("get_user", |cx| async move {
        let span = cx.span();
        span.set_attribute(KeyValue::new("user.id", user_id as i64));
        
        let start = std::time::Instant::now();
        
        // Simulate database query
        let user = fetch_user_from_db(user_id, &cx).await?;
        
        let duration = start.elapsed().as_millis() as f64;
        
        // Record metrics
        state.request_counter.add(1, &[
            KeyValue::new("http.method", "GET"),
            KeyValue::new("http.route", "/users/:id"),
            KeyValue::new("http.status", 200),
        ]);
        
        state.request_duration.record(duration, &[
            KeyValue::new("http.method", "GET"),
            KeyValue::new("http.route", "/users/:id"),
        ]);
        
        span.set_attribute(KeyValue::new("user.name", user.name.clone()));
        Ok(Json(user))
    }).await
}

async fn fetch_user_from_db(
    user_id: u64,
    cx: &opentelemetry::Context,
) -> Result<User, StatusCode> {
    let tracer = global::tracer("user-service");
    
    tracer.in_span_with_context("db.query", cx, |cx| async move {
        let span = cx.span();
        span.set_attribute(KeyValue::new("db.system", "postgresql"));
        span.set_attribute(KeyValue::new("db.statement", "SELECT * FROM users WHERE id = $1"));
        span.set_attribute(KeyValue::new("db.name", "users_db"));
        
        // Simulate database query
        tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;
        
        Ok(User {
            id: user_id,
            name: "John Doe".to_string(),
            email: "john@example.com".to_string(),
        })
    }).await
}

async fn create_user(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<User>,
) -> Result<Json<User>, StatusCode> {
    let tracer = global::tracer("user-service");
    
    tracer.in_span("create_user", |cx| async move {
        let span = cx.span();
        span.set_attribute(KeyValue::new("user.email", payload.email.clone()));
        
        let start = std::time::Instant::now();
        
        // Simulate database insert
        let user = insert_user_to_db(payload, &cx).await?;
        
        let duration = start.elapsed().as_millis() as f64;
        
        state.request_counter.add(1, &[
            KeyValue::new("http.method", "POST"),
            KeyValue::new("http.route", "/users"),
            KeyValue::new("http.status", 201),
        ]);
        
        state.request_duration.record(duration, &[
            KeyValue::new("http.method", "POST"),
            KeyValue::new("http.route", "/users"),
        ]);
        
        Ok(Json(user))
    }).await
}

async fn insert_user_to_db(
    user: User,
    cx: &opentelemetry::Context,
) -> Result<User, StatusCode> {
    let tracer = global::tracer("user-service");
    
    tracer.in_span_with_context("db.insert", cx, |cx| async move {
        let span = cx.span();
        span.set_attribute(KeyValue::new("db.system", "postgresql"));
        span.set_attribute(KeyValue::new("db.statement", "INSERT INTO users (name, email) VALUES ($1, $2)"));
        
        tokio::time::sleep(tokio::time::Duration::from_millis(15)).await;
        
        Ok(user)
    }).await
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let (tracer_provider, meter_provider) = init_telemetry();
    let state = Arc::new(init_metrics());
    
    let app = Router::new()
        .route("/users/:id", get(get_user))
        .route("/users", post(create_user))
        .layer(TraceLayer::new_for_http())
        .with_state(state);
    
    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await?;
    println!("Server running on http://localhost:3000");
    
    axum::serve(listener, app).await?;
    
    // Shutdown
    tracer_provider.shutdown()?;
    meter_provider.shutdown()?;
    
    Ok(())
}
```

## Example 2: Microservice with HTTP Client

```rust
use opentelemetry::{
    global,
    propagation::TextMapPropagator,
    trace::{TraceContextExt, Tracer},
    KeyValue,
};
use opentelemetry_http::HeaderInjector;
use reqwest::Client;
use std::collections::HashMap;

async fn call_downstream_service(order_id: &str) -> Result<String, Box<dyn std::error::Error>> {
    let tracer = global::tracer("order-service");
    
    tracer.in_span("call_inventory_service", |cx| async move {
        let span = cx.span();
        span.set_attribute(KeyValue::new("order.id", order_id.to_string()));
        span.set_attribute(KeyValue::new("peer.service", "inventory-service"));
        
        let mut headers = reqwest::header::HeaderMap::new();
        
        // Inject trace context into HTTP headers
        global::get_text_map_propagator(|propagator| {
            propagator.inject_context(&cx, &mut HeaderInjector(&mut headers));
        });
        
        let client = Client::new();
        let response = client
            .get(format!("http://inventory-service:8080/items/{}", order_id))
            .headers(headers)
            .send()
            .await?;
        
        span.set_attribute(KeyValue::new("http.status_code", response.status().as_u16() as i64));
        
        let body = response.text().await?;
        Ok(body)
    }).await
}

async fn process_order(order_id: &str) -> Result<(), Box<dyn std::error::Error>> {
    let tracer = global::tracer("order-service");
    
    tracer.in_span("process_order", |cx| async move {
        let span = cx.span();
        span.set_attribute(KeyValue::new("order.id", order_id.to_string()));
        
        // Call downstream service
        match call_downstream_service(order_id).await {
            Ok(items) => {
                span.set_attribute(KeyValue::new("items.count", items.len() as i64));
                Ok(())
            }
            Err(e) => {
                span.record_error(&*e);
                Err(e)
            }
        }
    }).await
}
```

## Example 3: Database Instrumentation with SQLx

```rust
use opentelemetry::{
    global,
    trace::{TraceContextExt, Tracer},
    KeyValue,
};
use sqlx::{Pool, Postgres};

async fn get_user_by_email(
    pool: &Pool<Postgres>,
    email: &str,
) -> Result<User, sqlx::Error> {
    let tracer = global::tracer("user-service");
    
    tracer.in_span("db.query.user_by_email", |cx| async move {
        let span = cx.span();
        
        // Set database semantic convention attributes
        span.set_attribute(KeyValue::new("db.system", "postgresql"));
        span.set_attribute(KeyValue::new("db.operation", "SELECT"));
        span.set_attribute(KeyValue::new("db.sql.table", "users"));
        span.set_attribute(KeyValue::new("db.statement", "SELECT * FROM users WHERE email = $1"));
        
        let result = sqlx::query_as::<_, User>(
            "SELECT id, name, email FROM users WHERE email = $1"
        )
        .bind(email)
        .fetch_one(pool)
        .await;
        
        match &result {
            Ok(user) => {
                span.set_attribute(KeyValue::new("db.rows_affected", 1));
                span.set_attribute(KeyValue::new("user.id", user.id as i64));
            }
            Err(e) => {
                span.record_error(e);
                span.set_attribute(KeyValue::new("db.rows_affected", 0));
            }
        }
        
        result
    }).await
}

async fn create_user(
    pool: &Pool<Postgres>,
    name: &str,
    email: &str,
) -> Result<User, sqlx::Error> {
    let tracer = global::tracer("user-service");
    
    tracer.in_span("db.query.create_user", |cx| async move {
        let span = cx.span();
        span.set_attribute(KeyValue::new("db.system", "postgresql"));
        span.set_attribute(KeyValue::new("db.operation", "INSERT"));
        span.set_attribute(KeyValue::new("db.sql.table", "users"));
        
        let result = sqlx::query_as::<_, User>(
            "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id, name, email"
        )
        .bind(name)
        .bind(email)
        .fetch_one(pool)
        .await;
        
        match &result {
            Ok(user) => {
                span.set_attribute(KeyValue::new("user.id", user.id as i64));
                span.set_attribute(KeyValue::new("db.rows_affected", 1));
            }
            Err(e) => {
                span.record_error(e);
            }
        }
        
        result
    }).await
}
```

## Example 4: Custom Metrics with Business Logic

```rust
use opentelemetry::{global, KeyValue};
use std::sync::Arc;
use tokio::sync::Mutex;

struct OrderProcessor {
    orders_processed: opentelemetry::metrics::Counter<u64>,
    order_value: opentelemetry::metrics::Histogram<f64>,
    active_orders: opentelemetry::metrics::UpDownCounter<i64>,
    revenue_total: Arc<Mutex<f64>>,
}

impl OrderProcessor {
    fn new() -> Self {
        let meter = global::meter("order-processor");
        
        let orders_processed = meter
            .u64_counter("orders.processed")
            .with_description("Total number of orders processed")
            .build();
        
        let order_value = meter
            .f64_histogram("orders.value")
            .with_unit("USD")
            .with_description("Order value distribution")
            .build();
        
        let active_orders = meter
            .i64_up_down_counter("orders.active")
            .with_description("Number of orders currently being processed")
            .build();
        
        let revenue_total = Arc::new(Mutex::new(0.0));
        let revenue_clone = revenue_total.clone();
        
        // Observable gauge for total revenue
        let _revenue_gauge = meter
            .f64_observable_gauge("revenue.total")
            .with_description("Total revenue")
            .with_unit("USD")
            .with_callback(move |observer| {
                let revenue = revenue_clone.blocking_lock();
                observer.observe(*revenue, &[]);
            })
            .build();
        
        Self {
            orders_processed,
            order_value,
            active_orders,
            revenue_total,
        }
    }
    
    async fn process_order(&self, order: Order) -> Result<(), Box<dyn std::error::Error>> {
        let tracer = global::tracer("order-processor");
        
        tracer.in_span("process_order", |cx| async move {
            let span = cx.span();
            span.set_attribute(KeyValue::new("order.id", order.id.clone()));
            span.set_attribute(KeyValue::new("order.customer", order.customer_id.clone()));
            
            // Track active orders
            self.active_orders.add(1, &[]);
            
            // Process the order
            let result = self.process_payment(&order).await;
            
            // Update metrics
            self.active_orders.add(-1, &[]);
            
            match result {
                Ok(_) => {
                    self.orders_processed.add(1, &[
                        KeyValue::new("status", "success"),
                        KeyValue::new("customer.type", order.customer_type.clone()),
                    ]);
                    
                    self.order_value.record(order.total, &[
                        KeyValue::new("customer.type", order.customer_type.clone()),
                    ]);
                    
                    // Update revenue
                    let mut revenue = self.revenue_total.lock().await;
                    *revenue += order.total;
                    
                    span.set_attribute(KeyValue::new("order.total", order.total));
                    Ok(())
                }
                Err(e) => {
                    self.orders_processed.add(1, &[
                        KeyValue::new("status", "error"),
                        KeyValue::new("customer.type", order.customer_type.clone()),
                    ]);
                    span.record_error(&*e);
                    Err(e)
                }
            }
        }).await
    }
    
    async fn process_payment(&self, order: &Order) -> Result<(), Box<dyn std::error::Error>> {
        let tracer = global::tracer("order-processor");
        
        tracer.in_span("process_payment", |cx| async move {
            let span = cx.span();
            span.set_attribute(KeyValue::new("payment.amount", order.total));
            span.set_attribute(KeyValue::new("payment.method", order.payment_method.clone()));
            
            // Simulate payment processing
            tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
            
            Ok(())
        }).await
    }
}

#[derive(Clone)]
struct Order {
    id: String,
    customer_id: String,
    customer_type: String,
    total: f64,
    payment_method: String,
}
```

## Example 5: Integration with Tracing for Structured Logging

```rust
use opentelemetry_appender_tracing::layer::OpenTelemetryTracingBridge;
use opentelemetry_sdk::logs::SdkLoggerProvider;
use tracing::{info, warn, error, instrument};
use tracing_subscriber::prelude::*;

fn init_logging() -> SdkLoggerProvider {
    let exporter = opentelemetry_otlp::LogExporter::builder()
        .with_http()
        .build()
        .expect("Failed to create log exporter");
    
    let provider = SdkLoggerProvider::builder()
        .with_batch_exporter(exporter)
        .with_resource(opentelemetry_sdk::Resource::builder()
            .with_service_name("my-service")
            .build())
        .build();
    
    let otel_layer = OpenTelemetryTracingBridge::new(&provider);
    
    tracing_subscriber::registry()
        .with(otel_layer)
        .with(tracing_subscriber::fmt::layer())
        .init();
    
    provider
}

#[instrument(skip(db_pool))]
async fn handle_user_request(
    user_id: u64,
    db_pool: &sqlx::PgPool,
) -> Result<User, Box<dyn std::error::Error>> {
    info!(user.id = user_id, "Processing user request");
    
    match fetch_user(db_pool, user_id).await {
        Ok(user) => {
            info!(
                user.id = user.id,
                user.email = %user.email,
                "User fetched successfully"
            );
            Ok(user)
        }
        Err(e) => {
            error!(
                user.id = user_id,
                error = %e,
                "Failed to fetch user"
            );
            Err(e)
        }
    }
}

#[instrument]
async fn fetch_user(
    pool: &sqlx::PgPool,
    user_id: u64,
) -> Result<User, sqlx::Error> {
    info!(user.id = user_id, "Querying database");
    
    sqlx::query_as::<_, User>("SELECT * FROM users WHERE id = $1")
        .bind(user_id)
        .fetch_one(pool)
        .await
}
```

## Example 6: Context Propagation Across Async Tasks

```rust
use opentelemetry::{global, Context};
use opentelemetry::trace::{TraceContextExt, Tracer};
use tokio::task;

async fn parallel_processing() {
    let tracer = global::tracer("my-service");
    
    tracer.in_span("parallel_parent", |cx| async move {
        let span = cx.span();
        span.set_attribute(KeyValue::new("operation", "parallel"));
        
        // Spawn multiple tasks with context
        let mut handles = vec![];
        
        for i in 0..5 {
            let cx_clone = cx.clone();
            let handle = task::spawn(async move {
                process_item(i, &cx_clone).await
            });
            handles.push(handle);
        }
        
        // Wait for all tasks
        for handle in handles {
            handle.await.unwrap();
        }
    }).await;
}

async fn process_item(item_id: usize, parent_cx: &Context) {
    let tracer = global::tracer("my-service");
    
    tracer.in_span_with_context(
        format!("process_item_{}", item_id),
        parent_cx,
        |cx| async move {
            let span = cx.span();
            span.set_attribute(KeyValue::new("item.id", item_id as i64));
            
            // Simulate work
            tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
            
            span.set_attribute(KeyValue::new("status", "completed"));
        }
    ).await;
}
```

## Example 7: Error Handling and Recording

```rust
use opentelemetry::{global, trace::{Status, TraceContextExt, Tracer}, KeyValue};
use thiserror::Error;

#[derive(Error, Debug)]
enum ServiceError {
    #[error("Database error: {0}")]
    Database(String),
    #[error("Validation error: {0}")]
    Validation(String),
    #[error("External service error: {0}")]
    ExternalService(String),
}

async fn handle_request_with_errors(
    request_id: &str,
) -> Result<String, ServiceError> {
    let tracer = global::tracer("my-service");
    
    tracer.in_span("handle_request", |cx| async move {
        let span = cx.span();
        span.set_attribute(KeyValue::new("request.id", request_id.to_string()));
        
        // Validate input
        if let Err(e) = validate_request(request_id) {
            span.record_error(&e);
            span.set_status(Status::error("Validation failed"));
            span.set_attribute(KeyValue::new("error.type", "validation"));
            return Err(e);
        }
        
        // Process request
        match process_data(request_id).await {
            Ok(result) => {
                span.set_status(Status::Ok);
                Ok(result)
            }
            Err(e) => {
                span.record_error(&e);
                span.set_status(Status::error("Processing failed"));
                span.set_attribute(KeyValue::new("error.type", "processing"));
                Err(e)
            }
        }
    }).await
}

fn validate_request(request_id: &str) -> Result<(), ServiceError> {
    if request_id.is_empty() {
        Err(ServiceError::Validation("Request ID cannot be empty".to_string()))
    } else {
        Ok(())
    }
}

async fn process_data(request_id: &str) -> Result<String, ServiceError> {
    // Simulate processing that might fail
    if request_id.starts_with("fail") {
        Err(ServiceError::Database("Connection timeout".to_string()))
    } else {
        Ok(format!("Processed: {}", request_id))
    }
}
```

These examples demonstrate common patterns for instrumenting Rust applications with OpenTelemetry, including HTTP services, database operations, distributed tracing, metrics collection, and error handling.
