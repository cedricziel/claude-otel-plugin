# OpenTelemetry Java Examples

> **Note**: These examples focus on key instrumentation patterns. Some imports and helper classes are abbreviated or omitted for clarity. In production code, ensure all necessary imports are included and helper classes are properly defined.

## Example 1: Simple HTTP Service with Manual Instrumentation

```java
import io.opentelemetry.api.GlobalOpenTelemetry;
import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.context.Scope;
import io.opentelemetry.context.propagation.TextMapGetter;
import io.opentelemetry.context.propagation.TextMapSetter;
import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.common.Attributes;

import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;

public class InstrumentedServlet extends HttpServlet {
    private static final Tracer tracer = 
        GlobalOpenTelemetry.getTracer("example-servlet", "1.0.0");
    
    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) 
            throws IOException {
        
        // Extract context from incoming request headers
        Context extractedContext = GlobalOpenTelemetry.getPropagators()
            .getTextMapPropagator()
            .extract(Context.current(), req, new HttpServletRequestGetter());
        
        // Create span with extracted context as parent
        Span span = tracer.spanBuilder("GET " + req.getRequestURI())
            .setParent(extractedContext)
            .setSpanKind(SpanKind.SERVER)
            .setAttribute("http.method", "GET")
            .setAttribute("http.url", req.getRequestURL().toString())
            .setAttribute("http.target", req.getRequestURI())
            .startSpan();
        
        try (Scope scope = span.makeCurrent()) {
            // Process request
            String userId = req.getParameter("userId");
            span.setAttribute("user.id", userId);
            
            String result = processRequest(userId);
            
            resp.setStatus(200);
            resp.getWriter().write(result);
            
            span.setAttribute("http.status_code", 200);
            span.setStatus(StatusCode.OK);
            
        } catch (Exception e) {
            span.setStatus(StatusCode.ERROR, "Request processing failed");
            span.recordException(e);
            resp.setStatus(500);
            throw e;
        } finally {
            span.end();
        }
    }
    
    private String processRequest(String userId) {
        Span span = tracer.spanBuilder("processRequest")
            .setAttribute("user.id", userId)
            .startSpan();
        
        try (Scope scope = span.makeCurrent()) {
            // Simulate some work
            Thread.sleep(100);
            return "Processed for user: " + userId;
        } catch (InterruptedException e) {
            span.recordException(e);
            throw new RuntimeException(e);
        } finally {
            span.end();
        }
    }
    
    // Helper to extract context from HTTP headers
    private static class HttpServletRequestGetter 
            implements TextMapGetter<HttpServletRequest> {
        @Override
        public Iterable<String> keys(HttpServletRequest carrier) {
            return Collections.list(carrier.getHeaderNames());
        }
        
        @Override
        public String get(HttpServletRequest carrier, String key) {
            return carrier.getHeader(key);
        }
    }
}
```

## Example 2: Database Service with Metrics

```java
import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.metrics.LongCounter;
import io.opentelemetry.api.metrics.Meter;
import io.opentelemetry.api.metrics.DoubleHistogram;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.context.Scope;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.ArrayList;
import java.util.List;

public class UserRepository {
    private final Tracer tracer;
    private final LongCounter queryCounter;
    private final DoubleHistogram queryDuration;
    private final Connection connection;
    
    public UserRepository(OpenTelemetry openTelemetry, Connection connection) {
        this.tracer = openTelemetry.getTracer("user-repository", "1.0.0");
        this.connection = connection;
        
        Meter meter = openTelemetry.getMeter("user-repository", "1.0.0");
        
        this.queryCounter = meter
            .counterBuilder("db.queries")
            .setDescription("Number of database queries")
            .setUnit("1")
            .build();
            
        this.queryDuration = meter
            .histogramBuilder("db.query.duration")
            .setDescription("Database query duration")
            .setUnit("ms")
            .build();
    }
    
    public List<User> findUsersByStatus(String status) {
        long startTime = System.currentTimeMillis();
        
        Span span = tracer.spanBuilder("SELECT users")
            .setSpanKind(SpanKind.CLIENT)
            .setAttribute("db.system", "postgresql")
            .setAttribute("db.name", "myapp")
            .setAttribute("db.operation", "SELECT")
            .setAttribute("db.sql.table", "users")
            .startSpan();
        
        try (Scope scope = span.makeCurrent()) {
            String sql = "SELECT id, name, email FROM users WHERE status = ?";
            span.setAttribute("db.statement", sql);
            
            try (PreparedStatement stmt = connection.prepareStatement(sql)) {
                stmt.setString(1, status);
                
                try (ResultSet rs = stmt.executeQuery()) {
                    List<User> users = new ArrayList<>();
                    int rowCount = 0;
                    
                    while (rs.next()) {
                        users.add(new User(
                            rs.getLong("id"),
                            rs.getString("name"),
                            rs.getString("email")
                        ));
                        rowCount++;
                    }
                    
                    span.setAttribute("db.rows_returned", rowCount);
                    
                    // Record metrics
                    Attributes attributes = Attributes.of(
                        AttributeKey.stringKey("db.operation"), "SELECT",
                        AttributeKey.stringKey("db.table"), "users",
                        AttributeKey.stringKey("status"), "success"
                    );
                    
                    queryCounter.add(1, attributes);
                    queryDuration.record(
                        System.currentTimeMillis() - startTime, 
                        attributes
                    );
                    
                    return users;
                }
            }
        } catch (Exception e) {
            span.setStatus(StatusCode.ERROR, "Query failed");
            span.recordException(e);
            
            // Record error metrics
            Attributes attributes = Attributes.of(
                AttributeKey.stringKey("db.operation"), "SELECT",
                AttributeKey.stringKey("db.table"), "users",
                AttributeKey.stringKey("status"), "error"
            );
            
            queryCounter.add(1, attributes);
            
            throw new RuntimeException("Failed to fetch users", e);
        } finally {
            span.end();
        }
    }
}

class User {
    private Long id;
    private String name;
    private String email;
    
    public User(Long id, String name, String email) {
        this.id = id;
        this.name = name;
        this.email = email;
    }
    
    // Getters and setters...
}
```

## Example 3: Microservice with HTTP Client Instrumentation

```java
import io.opentelemetry.api.GlobalOpenTelemetry;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Scope;
import io.opentelemetry.context.propagation.TextMapSetter;
import io.opentelemetry.api.trace.SpanKind;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class OrderService {
    private final Tracer tracer;
    private final HttpClient httpClient;
    
    public OrderService() {
        this.tracer = GlobalOpenTelemetry.getTracer("order-service", "1.0.0");
        this.httpClient = HttpClient.newHttpClient();
    }
    
    public Order createOrder(OrderRequest request) {
        Span span = tracer.spanBuilder("createOrder")
            .setSpanKind(SpanKind.INTERNAL)
            .setAttribute("order.items_count", request.getItems().size())
            .startSpan();
        
        try (Scope scope = span.makeCurrent()) {
            // Validate order
            validateOrder(request);
            
            // Check inventory
            boolean available = checkInventory(request);
            span.setAttribute("inventory.available", available);
            
            if (!available) {
                span.addEvent("Insufficient inventory");
                throw new RuntimeException("Items not available");
            }
            
            // Process payment
            String paymentId = processPayment(request);
            span.setAttribute("payment.id", paymentId);
            
            // Create order
            Order order = saveOrder(request, paymentId);
            span.setAttribute("order.id", order.getId());
            
            return order;
            
        } catch (Exception e) {
            span.setStatus(StatusCode.ERROR, "Order creation failed");
            span.recordException(e);
            throw e;
        } finally {
            span.end();
        }
    }
    
    private boolean checkInventory(OrderRequest request) {
        Span span = tracer.spanBuilder("GET /inventory/check")
            .setSpanKind(SpanKind.CLIENT)
            .setAttribute("http.method", "GET")
            .setAttribute("http.url", "http://inventory-service/api/check")
            .startSpan();
        
        try (Scope scope = span.makeCurrent()) {
            // Build request
            HttpRequest.Builder requestBuilder = HttpRequest.newBuilder()
                .uri(URI.create("http://inventory-service/api/check"))
                .GET();
            
            // Inject trace context into headers
            GlobalOpenTelemetry.getPropagators()
                .getTextMapPropagator()
                .inject(
                    Context.current(), 
                    requestBuilder, 
                    new HttpRequestSetter()
                );
            
            HttpRequest httpRequest = requestBuilder.build();
            
            // Send request
            HttpResponse<String> response = httpClient.send(
                httpRequest, 
                HttpResponse.BodyHandlers.ofString()
            );
            
            span.setAttribute("http.status_code", response.statusCode());
            
            if (response.statusCode() == 200) {
                return Boolean.parseBoolean(response.body());
            } else {
                span.setStatus(StatusCode.ERROR, "Inventory check failed");
                throw new RuntimeException("Inventory service error");
            }
            
        } catch (Exception e) {
            span.recordException(e);
            throw new RuntimeException("Failed to check inventory", e);
        } finally {
            span.end();
        }
    }
    
    private String processPayment(OrderRequest request) {
        // Similar pattern as checkInventory
        return "payment-123";
    }
    
    private void validateOrder(OrderRequest request) {
        Span span = tracer.spanBuilder("validateOrder").startSpan();
        try (Scope scope = span.makeCurrent()) {
            // Validation logic
        } finally {
            span.end();
        }
    }
    
    private Order saveOrder(OrderRequest request, String paymentId) {
        // Save to database
        return new Order("order-123", paymentId);
    }
    
    // Helper to inject context into HTTP headers
    private static class HttpRequestSetter 
            implements TextMapSetter<HttpRequest.Builder> {
        @Override
        public void set(HttpRequest.Builder carrier, String key, String value) {
            if (carrier != null && key != null && value != null) {
                carrier.header(key, value);
            }
        }
    }
}
```

## Example 4: Spring Boot REST Controller

```java
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Scope;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/products")
public class ProductController {
    
    @Autowired
    private Tracer tracer;
    
    @Autowired
    private ProductService productService;
    
    @GetMapping("/{id}")
    public Product getProduct(@PathVariable String id) {
        Span span = tracer.spanBuilder("ProductController.getProduct")
            .setAttribute("product.id", id)
            .startSpan();
        
        try (Scope scope = span.makeCurrent()) {
            Product product = productService.findById(id);
            
            if (product == null) {
                span.addEvent("Product not found");
                span.setAttribute("product.found", false);
                throw new ProductNotFoundException(id);
            }
            
            span.setAttribute("product.found", true);
            span.setAttribute("product.category", product.getCategory());
            
            return product;
            
        } catch (ProductNotFoundException e) {
            span.recordException(e);
            throw e;
        } finally {
            span.end();
        }
    }
    
    @PostMapping
    public Product createProduct(@RequestBody Product product) {
        Span span = tracer.spanBuilder("ProductController.createProduct")
            .setAttribute("product.name", product.getName())
            .setAttribute("product.category", product.getCategory())
            .startSpan();
        
        try (Scope scope = span.makeCurrent()) {
            Product created = productService.create(product);
            span.setAttribute("product.id", created.getId());
            return created;
        } finally {
            span.end();
        }
    }
}
```

## Example 5: Async Processing with CompletableFuture

```java
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Context;
import io.opentelemetry.context.Scope;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class AsyncProcessor {
    private final Tracer tracer;
    private final ExecutorService executor;
    
    public AsyncProcessor(OpenTelemetry openTelemetry) {
        this.tracer = openTelemetry.getTracer("async-processor", "1.0.0");
        this.executor = Executors.newFixedThreadPool(10);
    }
    
    public CompletableFuture<String> processAsync(String data) {
        Span span = tracer.spanBuilder("processAsync")
            .setAttribute("data.length", data.length())
            .startSpan();
        
        // Capture current context
        Context context = Context.current().with(span);
        
        return CompletableFuture.supplyAsync(() -> {
            // Make context current in async thread
            try (Scope scope = context.makeCurrent()) {
                Span asyncSpan = tracer.spanBuilder("async-work").startSpan();
                
                try (Scope asyncScope = asyncSpan.makeCurrent()) {
                    // Do async work
                    String result = performWork(data);
                    asyncSpan.setAttribute("result.length", result.length());
                    return result;
                } finally {
                    asyncSpan.end();
                }
            }
        }, executor)
        .whenComplete((result, error) -> {
            if (error != null) {
                span.setStatus(StatusCode.ERROR, "Async processing failed");
                span.recordException(error);
            }
            span.end();
        });
    }
    
    private String performWork(String data) {
        // Simulate work
        try {
            Thread.sleep(100);
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
        return data.toUpperCase();
    }
}
```

These examples demonstrate common patterns for instrumenting Java applications with OpenTelemetry, including HTTP services, database operations, microservice communication, Spring Boot integration, and async processing.
