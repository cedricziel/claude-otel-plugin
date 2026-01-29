---
name: opentelemetry-js
description: Expert knowledge for instrumenting JavaScript, TypeScript, React, and Node.js applications with OpenTelemetry. Use when working with JavaScript/TypeScript code instrumentation, adding observability to Node.js applications, Express.js servers, React frontends, Next.js applications, or when asked about OpenTelemetry in JavaScript/TypeScript, tracing, metrics, spans, distributed tracing in JS/TS, OTLP exporters, or instrumentation libraries for Node.js, React, Express, Next.js, GraphQL, databases (PostgreSQL, MongoDB, MySQL), or browser-based applications.
---

# OpenTelemetry JavaScript Instrumentation

Expert guidance for instrumenting JavaScript and TypeScript applications with OpenTelemetry across Node.js and browser environments.

## Quick Start

### Node.js Automatic Instrumentation

Install required packages:
```bash
npm install --save @opentelemetry/sdk-node \
  @opentelemetry/auto-instrumentations-node \
  @opentelemetry/exporter-trace-otlp-http
```

Create `instrumentation.js`:
```javascript
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'your-service-name',
  }),
  traceExporter: new OTLPTraceExporter({
    url: 'http://localhost:4318/v1/traces',
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();
```

Run your application:
```bash
node --require ./instrumentation.js app.js
```

## Core Instrumentation Patterns

### Manual Span Creation

```javascript
const { trace, SpanStatusCode } = require('@opentelemetry/api');

const tracer = trace.getTracer('my-service');

async function processRequest(req) {
  const span = tracer.startSpan('process-request');
  
  try {
    span.setAttribute('user.id', req.userId);
    const result = await doWork();
    span.setStatus({ code: SpanStatusCode.OK });
    return result;
  } catch (error) {
    span.recordException(error);
    span.setStatus({ code: SpanStatusCode.ERROR });
    throw error;
  } finally {
    span.end();
  }
}
```

### Context Propagation

Always use context for parent-child span relationships:

```javascript
const opentelemetry = require('@opentelemetry/api');

const parentSpan = tracer.startSpan('parent-operation');
const ctx = opentelemetry.trace.setSpan(opentelemetry.context.active(), parentSpan);

// Create child span with proper context
const childSpan = tracer.startSpan('child-operation', {}, ctx);
```

## Framework-Specific Instrumentation

### Express.js

Use automatic instrumentation:
```javascript
const { ExpressInstrumentation } = require('@opentelemetry/instrumentation-express');
const { HttpInstrumentation } = require('@opentelemetry/instrumentation-http');
const { registerInstrumentations } = require('@opentelemetry/instrumentation');

registerInstrumentations({
  instrumentations: [
    new HttpInstrumentation(),
    new ExpressInstrumentation(),
  ],
});
```

### React (Browser)

```javascript
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { DocumentLoadInstrumentation } from '@opentelemetry/instrumentation-document-load';
import { UserInteractionInstrumentation } from '@opentelemetry/instrumentation-user-interaction';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { ZoneContextManager } from '@opentelemetry/context-zone';

const provider = new WebTracerProvider({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'browser-app',
  }),
});

provider.addSpanProcessor(new BatchSpanProcessor(
  new OTLPTraceExporter({ url: 'http://localhost:4318/v1/traces' })
));

provider.register({
  contextManager: new ZoneContextManager(),
});

registerInstrumentations({
  instrumentations: [
    new DocumentLoadInstrumentation(),
    new UserInteractionInstrumentation(),
  ],
});
```

### Next.js (App Router)

Create `instrumentation.ts` in project root:
```typescript
export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    const { NodeSDK } = await import('@opentelemetry/sdk-node');
    const { getNodeAutoInstrumentations } = await import('@opentelemetry/auto-instrumentations-node');
    
    const sdk = new NodeSDK({
      instrumentations: [getNodeAutoInstrumentations()],
    });
    
    sdk.start();
  }
}
```

Enable in `next.config.js`:
```javascript
module.exports = {
  experimental: {
    instrumentationHook: true,
  },
};
```

## Database Instrumentation

### PostgreSQL
```bash
npm install @opentelemetry/instrumentation-pg
```

```javascript
const { PgInstrumentation } = require('@opentelemetry/instrumentation-pg');
registerInstrumentations({
  instrumentations: [new PgInstrumentation()],
});
```

### MongoDB
```bash
npm install @opentelemetry/instrumentation-mongodb
```

### MySQL
```bash
npm install @opentelemetry/instrumentation-mysql2
```

## Metrics

### Creating Metrics

```javascript
const { metrics } = require('@opentelemetry/api');
const meter = metrics.getMeter('my-service');

// Counter
const requestCounter = meter.createCounter('http.requests');
requestCounter.add(1, { 'http.method': 'GET' });

// Histogram
const requestDuration = meter.createHistogram('http.request.duration', { unit: 'ms' });
requestDuration.record(150, { 'http.method': 'GET' });

// UpDownCounter
const activeConnections = meter.createUpDownCounter('http.active_connections');
activeConnections.add(1);  // Connection opened
activeConnections.add(-1); // Connection closed

// Observable Gauge
const memoryUsage = meter.createObservableGauge('process.memory.usage', { unit: 'bytes' });
memoryUsage.addCallback((result) => {
  result.observe(process.memoryUsage().heapUsed, { type: 'heap' });
});
```

## Environment Configuration

```bash
# Service identification
OTEL_SERVICE_NAME=your-service-name
OTEL_RESOURCE_ATTRIBUTES=service.version=1.0.0,deployment.environment=production

# Exporter configuration
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://localhost:4318/v1/traces
OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://localhost:4318/v1/metrics

# Sampling
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1
```

## Best Practices

1. **Initialize early** - Set up OpenTelemetry before importing other modules
2. **Use semantic conventions** - Follow OpenTelemetry semantic conventions for attribute names
3. **Context propagation** - Always use `context.with()` for async operations
4. **Resource attributes** - Always set `service.name` and other relevant attributes
5. **Error handling** - Always record exceptions with `span.recordException(error)`
6. **Span lifecycle** - Always call `span.end()` in finally blocks
7. **Meaningful names** - Use descriptive, low-cardinality span names
8. **Batch processing** - Use `BatchSpanProcessor` for better performance
9. **Sampling** - Implement appropriate sampling strategies for production
10. **TypeScript** - Use TypeScript for better type safety

## Advanced Topics

For detailed examples and advanced patterns, see [references/examples.md](references/examples.md).

## Troubleshooting

### Spans not appearing
- Check SDK is initialized before other modules
- Verify exporter endpoint is correct and accessible
- Ensure `span.end()` is called

### Context not propagating
- Verify context manager is properly configured
- Use `context.with()` for async operations
- Check instrumentations are registered before modules are imported

### Performance issues
- Adjust batch processor settings
- Implement appropriate sampling
- Reduce attribute cardinality

## Key NPM Packages

- `@opentelemetry/api` - Core API
- `@opentelemetry/sdk-node` - Node.js SDK
- `@opentelemetry/auto-instrumentations-node` - Automatic Node.js instrumentation
- `@opentelemetry/sdk-trace-web` - Browser SDK
- `@opentelemetry/instrumentation-express` - Express instrumentation
- `@opentelemetry/instrumentation-http` - HTTP instrumentation
- `@opentelemetry/instrumentation-pg` - PostgreSQL instrumentation
- `@opentelemetry/instrumentation-mongodb` - MongoDB instrumentation
- `@opentelemetry/instrumentation-graphql` - GraphQL instrumentation

## Resources

- [OpenTelemetry JavaScript Docs](https://opentelemetry.io/docs/languages/js/)
- [OpenTelemetry JS GitHub](https://github.com/open-telemetry/opentelemetry-js)
- [OpenTelemetry JS Contrib](https://github.com/open-telemetry/opentelemetry-js-contrib)
