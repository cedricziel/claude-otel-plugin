# OpenTelemetry JavaScript Instrumentation Guide

## Overview

OpenTelemetry JavaScript provides comprehensive observability for JavaScript and TypeScript applications across Node.js and browser environments. This guide covers automatic and manual instrumentation approaches for the JavaScript ecosystem including Node.js, React, Express, Next.js, and other popular frameworks.

## Node.js Automatic Instrumentation

The easiest way to instrument a Node.js application is using automatic instrumentation with the SDK.

### Setup with Auto-Instrumentation

1. Install required packages:
```bash
npm install --save @opentelemetry/sdk-node \
  @opentelemetry/auto-instrumentations-node \
  @opentelemetry/exporter-trace-otlp-http
```

2. Create an instrumentation file (e.g., `instrumentation.js` or `tracing.js`):
```javascript
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'your-service-name',
    [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0',
  }),
  traceExporter: new OTLPTraceExporter({
    url: 'http://localhost:4318/v1/traces',
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();

process.on('SIGTERM', () => {
  sdk.shutdown()
    .then(() => console.log('Tracing terminated'))
    .catch((error) => console.log('Error terminating tracing', error))
    .finally(() => process.exit(0));
});
```

3. Start your application with the instrumentation:
```bash
node --require ./instrumentation.js app.js
```

Or use the `NODE_OPTIONS` environment variable:
```bash
NODE_OPTIONS='--require ./instrumentation.js' node app.js
```

### TypeScript Auto-Instrumentation

For TypeScript applications, use `ts-node` or compile first:

```bash
# Using ts-node
NODE_OPTIONS='--require ./instrumentation.ts' ts-node app.ts

# Or compile and run
tsc
NODE_OPTIONS='--require ./dist/instrumentation.js' node dist/app.js
```

## Manual Instrumentation

For more control over instrumentation, use manual instrumentation with the OpenTelemetry API.

### NPM Dependencies

```bash
npm install --save @opentelemetry/api \
  @opentelemetry/sdk-trace-node \
  @opentelemetry/sdk-metrics \
  @opentelemetry/exporter-trace-otlp-http \
  @opentelemetry/exporter-metrics-otlp-http \
  @opentelemetry/resources \
  @opentelemetry/semantic-conventions
```

### Initialize OpenTelemetry SDK

```javascript
const opentelemetry = require('@opentelemetry/api');
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');
const { BatchSpanProcessor } = require('@opentelemetry/sdk-trace-base');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');

// Create a tracer provider
const provider = new NodeTracerProvider({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'your-service',
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: 'production',
  }),
});

// Configure span processor and exporter
const exporter = new OTLPTraceExporter({
  url: 'http://localhost:4318/v1/traces',
});
provider.addSpanProcessor(new BatchSpanProcessor(exporter));

// Register the provider
provider.register();

// Get a tracer
const tracer = opentelemetry.trace.getTracer('my-service-tracer', '1.0.0');
```

### Creating Spans

```javascript
const span = tracer.startSpan('operation-name');

// Add attributes to the span
span.setAttribute('user.id', userId);
span.setAttribute('custom.key', 'custom-value');

try {
  // Perform operation
  const result = performOperation();
  span.setStatus({ code: opentelemetry.SpanStatusCode.OK });
  return result;
} catch (error) {
  span.recordException(error);
  span.setStatus({
    code: opentelemetry.SpanStatusCode.ERROR,
    message: error.message,
  });
  throw error;
} finally {
  span.end();
}
```

### Context Propagation

```javascript
const opentelemetry = require('@opentelemetry/api');

// Start a span and make it active
const span = tracer.startSpan('parent-operation');
const ctx = opentelemetry.trace.setSpan(opentelemetry.context.active(), span);

// Run code in the context
opentelemetry.context.with(ctx, () => {
  // This operation will be a child of the parent span
  childOperation();
});

span.end();
```

### Async Context Propagation

```javascript
async function processRequest() {
  const span = tracer.startSpan('process-request');
  
  try {
    await opentelemetry.context.with(
      opentelemetry.trace.setSpan(opentelemetry.context.active(), span),
      async () => {
        // All async operations here will have correct context
        await fetchData();
        await saveData();
      }
    );
    span.setStatus({ code: opentelemetry.SpanStatusCode.OK });
  } catch (error) {
    span.recordException(error);
    span.setStatus({ code: opentelemetry.SpanStatusCode.ERROR });
    throw error;
  } finally {
    span.end();
  }
}
```

## Express.js Instrumentation

### Automatic with Auto-Instrumentation

Auto-instrumentation automatically instruments Express.js when using `@opentelemetry/auto-instrumentations-node`.

### Manual Express Instrumentation

```bash
npm install --save @opentelemetry/instrumentation-express \
  @opentelemetry/instrumentation-http
```

```javascript
const { ExpressInstrumentation } = require('@opentelemetry/instrumentation-express');
const { HttpInstrumentation } = require('@opentelemetry/instrumentation-http');
const { registerInstrumentations } = require('@opentelemetry/instrumentation');

// Register instrumentations
registerInstrumentations({
  instrumentations: [
    new HttpInstrumentation(),
    new ExpressInstrumentation(),
  ],
});

// Then import and use Express as normal
const express = require('express');
const app = express();
```

### Adding Custom Spans to Express Routes

```javascript
const opentelemetry = require('@opentelemetry/api');

app.get('/users/:id', async (req, res) => {
  const tracer = opentelemetry.trace.getTracer('my-app');
  const span = tracer.startSpan('fetch-user', {
    attributes: {
      'user.id': req.params.id,
    },
  });

  try {
    const user = await getUserById(req.params.id);
    span.setAttribute('user.found', !!user);
    res.json(user);
    span.setStatus({ code: opentelemetry.SpanStatusCode.OK });
  } catch (error) {
    span.recordException(error);
    span.setStatus({ code: opentelemetry.SpanStatusCode.ERROR });
    res.status(500).json({ error: error.message });
  } finally {
    span.end();
  }
});
```

## React and Browser Instrumentation

### Browser SDK Setup

```bash
npm install --save @opentelemetry/sdk-trace-web \
  @opentelemetry/instrumentation-document-load \
  @opentelemetry/instrumentation-user-interaction \
  @opentelemetry/exporter-trace-otlp-http \
  @opentelemetry/context-zone
```

### Browser Instrumentation Setup

```javascript
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { DocumentLoadInstrumentation } from '@opentelemetry/instrumentation-document-load';
import { UserInteractionInstrumentation } from '@opentelemetry/instrumentation-user-interaction';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { ZoneContextManager } from '@opentelemetry/context-zone';

const provider = new WebTracerProvider({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'browser-app',
  }),
});

const exporter = new OTLPTraceExporter({
  url: 'http://localhost:4318/v1/traces',
});

provider.addSpanProcessor(new BatchSpanProcessor(exporter));
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

### React Component Instrumentation

```javascript
import { trace } from '@opentelemetry/api';
import { useEffect } from 'react';

const tracer = trace.getTracer('react-app');

function UserProfile({ userId }) {
  useEffect(() => {
    const span = tracer.startSpan('fetch-user-profile');
    span.setAttribute('user.id', userId);

    fetchUserProfile(userId)
      .then((profile) => {
        span.setAttribute('profile.loaded', true);
        span.setStatus({ code: SpanStatusCode.OK });
      })
      .catch((error) => {
        span.recordException(error);
        span.setStatus({ code: SpanStatusCode.ERROR });
      })
      .finally(() => {
        span.end();
      });
  }, [userId]);

  return <div>User Profile</div>;
}
```

### React Custom Hook for Tracing

```typescript
import { trace, Span, SpanStatusCode } from '@opentelemetry/api';
import { useEffect, useRef } from 'react';

export function useTracing(operationName: string, attributes?: Record<string, any>) {
  const spanRef = useRef<Span | null>(null);

  useEffect(() => {
    const tracer = trace.getTracer('react-app');
    spanRef.current = tracer.startSpan(operationName, { attributes });

    return () => {
      if (spanRef.current) {
        spanRef.current.setStatus({ code: SpanStatusCode.OK });
        spanRef.current.end();
      }
    };
  }, [operationName]);

  return {
    recordError: (error: Error) => {
      spanRef.current?.recordException(error);
      spanRef.current?.setStatus({ code: SpanStatusCode.ERROR });
    },
    setAttribute: (key: string, value: any) => {
      spanRef.current?.setAttribute(key, value);
    },
  };
}
```

## Next.js Instrumentation

### Next.js 13+ App Router

Create `instrumentation.ts` in the root of your Next.js project:

```typescript
// instrumentation.ts
export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    const { NodeSDK } = await import('@opentelemetry/sdk-node');
    const { getNodeAutoInstrumentations } = await import('@opentelemetry/auto-instrumentations-node');
    const { OTLPTraceExporter } = await import('@opentelemetry/exporter-trace-otlp-http');
    const { Resource } = await import('@opentelemetry/resources');
    const { SemanticResourceAttributes } = await import('@opentelemetry/semantic-conventions');

    const sdk = new NodeSDK({
      resource: new Resource({
        [SemanticResourceAttributes.SERVICE_NAME]: 'nextjs-app',
      }),
      traceExporter: new OTLPTraceExporter({
        url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4318/v1/traces',
      }),
      instrumentations: [getNodeAutoInstrumentations()],
    });

    sdk.start();
  }
}
```

Enable instrumentation in `next.config.js`:

```javascript
// next.config.js
module.exports = {
  experimental: {
    instrumentationHook: true,
  },
};
```

### Next.js API Routes

```typescript
// pages/api/users/[id].ts
import { trace } from '@opentelemetry/api';
import type { NextApiRequest, NextApiResponse } from 'next';

const tracer = trace.getTracer('nextjs-api');

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const span = tracer.startSpan('get-user-api', {
    attributes: {
      'http.method': req.method,
      'user.id': req.query.id,
    },
  });

  try {
    const user = await getUserById(req.query.id as string);
    span.setAttribute('user.found', !!user);
    res.status(200).json(user);
    span.setStatus({ code: SpanStatusCode.OK });
  } catch (error) {
    span.recordException(error as Error);
    span.setStatus({ code: SpanStatusCode.ERROR });
    res.status(500).json({ error: 'Internal server error' });
  } finally {
    span.end();
  }
}
```

## Database Instrumentation

### PostgreSQL (pg)

```bash
npm install --save @opentelemetry/instrumentation-pg
```

```javascript
const { PgInstrumentation } = require('@opentelemetry/instrumentation-pg');
const { registerInstrumentations } = require('@opentelemetry/instrumentation');

registerInstrumentations({
  instrumentations: [
    new PgInstrumentation(),
  ],
});

// Use pg as normal
const { Pool } = require('pg');
const pool = new Pool();
```

### MongoDB

```bash
npm install --save @opentelemetry/instrumentation-mongodb
```

```javascript
const { MongoDBInstrumentation } = require('@opentelemetry/instrumentation-mongodb');
const { registerInstrumentations } = require('@opentelemetry/instrumentation');

registerInstrumentations({
  instrumentations: [
    new MongoDBInstrumentation(),
  ],
});
```

### MySQL

```bash
npm install --save @opentelemetry/instrumentation-mysql2
```

```javascript
const { MySQL2Instrumentation } = require('@opentelemetry/instrumentation-mysql2');
const { registerInstrumentations } = require('@opentelemetry/instrumentation');

registerInstrumentations({
  instrumentations: [
    new MySQL2Instrumentation(),
  ],
});
```

## Metrics

### Setting Up Metrics

```bash
npm install --save @opentelemetry/sdk-metrics \
  @opentelemetry/exporter-metrics-otlp-http
```

```javascript
const { MeterProvider, PeriodicExportingMetricReader } = require('@opentelemetry/sdk-metrics');
const { OTLPMetricExporter } = require('@opentelemetry/exporter-metrics-otlp-http');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');

const meterProvider = new MeterProvider({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'your-service',
  }),
});

const metricExporter = new OTLPMetricExporter({
  url: 'http://localhost:4318/v1/metrics',
});

meterProvider.addMetricReader(
  new PeriodicExportingMetricReader({
    exporter: metricExporter,
    exportIntervalMillis: 60000, // Export every 60 seconds
  })
);

// Register the meter provider
const { metrics } = require('@opentelemetry/api');
metrics.setGlobalMeterProvider(meterProvider);
```

### Creating and Using Metrics

```javascript
const { metrics } = require('@opentelemetry/api');

const meter = metrics.getMeter('my-service-meter');

// Counter
const requestCounter = meter.createCounter('http.requests', {
  description: 'Count of HTTP requests',
});
requestCounter.add(1, { 'http.method': 'GET', 'http.route': '/users' });

// Histogram
const requestDuration = meter.createHistogram('http.request.duration', {
  description: 'HTTP request duration in milliseconds',
  unit: 'ms',
});
requestDuration.record(150, { 'http.method': 'GET', 'http.route': '/users' });

// UpDownCounter
const activeConnections = meter.createUpDownCounter('http.active_connections', {
  description: 'Number of active HTTP connections',
});
activeConnections.add(1); // Connection opened
activeConnections.add(-1); // Connection closed

// Observable Gauge
const memoryUsage = meter.createObservableGauge('process.memory.usage', {
  description: 'Current memory usage',
  unit: 'bytes',
});
memoryUsage.addCallback((observableResult) => {
  const memUsage = process.memoryUsage();
  observableResult.observe(memUsage.heapUsed, { type: 'heap' });
  observableResult.observe(memUsage.rss, { type: 'rss' });
});
```

## GraphQL Instrumentation

```bash
npm install --save @opentelemetry/instrumentation-graphql
```

```javascript
const { GraphQLInstrumentation } = require('@opentelemetry/instrumentation-graphql');
const { registerInstrumentations } = require('@opentelemetry/instrumentation');

registerInstrumentations({
  instrumentations: [
    new GraphQLInstrumentation({
      // Options
      mergeItems: true,
      allowValues: true,
    }),
  ],
});
```

## Context Propagation with HTTP

### Server-Side (Extracting Context)

```javascript
const opentelemetry = require('@opentelemetry/api');

app.use((req, res, next) => {
  // Extract context from incoming request headers
  const extractedContext = opentelemetry.propagation.extract(
    opentelemetry.context.active(),
    req.headers
  );

  // Run the rest of the request in the extracted context
  opentelemetry.context.with(extractedContext, () => {
    next();
  });
});
```

### Client-Side (Injecting Context)

```javascript
const opentelemetry = require('@opentelemetry/api');
const axios = require('axios');

async function makeRequest() {
  const span = tracer.startSpan('http-request');
  
  try {
    // Create headers object
    const headers = {};
    
    // Inject current context into headers
    opentelemetry.propagation.inject(
      opentelemetry.trace.setSpan(opentelemetry.context.active(), span),
      headers
    );

    const response = await axios.get('http://api.example.com/data', { headers });
    span.setStatus({ code: opentelemetry.SpanStatusCode.OK });
    return response.data;
  } catch (error) {
    span.recordException(error);
    span.setStatus({ code: opentelemetry.SpanStatusCode.ERROR });
    throw error;
  } finally {
    span.end();
  }
}
```

## Sampling

### Probability Sampler

```javascript
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { ParentBasedSampler, TraceIdRatioBasedSampler } = require('@opentelemetry/sdk-trace-base');

const provider = new NodeTracerProvider({
  sampler: new ParentBasedSampler({
    root: new TraceIdRatioBasedSampler(0.1), // Sample 10% of traces
  }),
});
```

### Custom Sampler

```javascript
const { SamplingDecision } = require('@opentelemetry/sdk-trace-base');

class CustomSampler {
  shouldSample(context, traceId, spanName, spanKind, attributes) {
    // Sample all errors
    if (attributes['http.status_code'] >= 400) {
      return {
        decision: SamplingDecision.RECORD_AND_SAMPLED,
      };
    }

    // Sample 1% of successful requests
    if (Math.random() < 0.01) {
      return {
        decision: SamplingDecision.RECORD_AND_SAMPLED,
      };
    }

    return {
      decision: SamplingDecision.NOT_RECORD,
    };
  }

  toString() {
    return 'CustomSampler';
  }
}

const provider = new NodeTracerProvider({
  sampler: new CustomSampler(),
});
```

## Environment Variables Configuration

Key environment variables for OpenTelemetry JavaScript:

```bash
# Service identification
OTEL_SERVICE_NAME=your-service-name
OTEL_RESOURCE_ATTRIBUTES=service.version=1.0.0,deployment.environment=production

# Exporter configuration
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://localhost:4318/v1/traces
OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://localhost:4318/v1/metrics

# Headers (e.g., for authentication)
OTEL_EXPORTER_OTLP_HEADERS=api-key=your-api-key

# Protocol (http/protobuf or grpc)
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf

# Sampling
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1

# Logging
OTEL_LOG_LEVEL=info
```

## Best Practices

1. **Initialize early**: Set up OpenTelemetry before importing other modules
2. **Use semantic conventions**: Follow OpenTelemetry semantic conventions for attribute names
3. **Proper context propagation**: Ensure context is properly propagated in async operations
4. **Resource attributes**: Always set service.name and other relevant resource attributes
5. **Error handling**: Always record exceptions and set error status on spans
6. **Span lifecycle**: Always call `span.end()` in finally blocks to ensure spans are completed
7. **Meaningful span names**: Use descriptive, low-cardinality span names
8. **Batch processing**: Use BatchSpanProcessor for better performance
9. **Sampling**: Implement appropriate sampling strategies for production
10. **TypeScript**: Use TypeScript for better type safety and IDE support

## Troubleshooting

### Spans not appearing

- Check that the SDK is initialized before other modules are imported
- Verify exporter endpoint is correct and accessible
- Check for errors in SDK initialization
- Ensure `span.end()` is called

### Context not propagating

- Verify context manager is properly configured
- Use `context.with()` for async operations
- Check that instrumentations are registered before modules are imported

### Performance issues

- Adjust batch processor settings
- Implement appropriate sampling
- Reduce attribute cardinality
- Use async exporters

### TypeScript errors

- Ensure `@opentelemetry/api` types are installed
- Check TypeScript version compatibility
- Verify tsconfig.json includes proper module resolution
