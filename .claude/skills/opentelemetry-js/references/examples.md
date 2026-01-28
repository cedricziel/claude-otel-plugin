# OpenTelemetry JavaScript Examples

> **Note**: These examples focus on key instrumentation patterns for the JavaScript ecosystem. Some imports and configuration details may be abbreviated for clarity. In production code, ensure all necessary packages are installed and properly configured.

## Example 1: Express.js REST API with Full Instrumentation

```javascript
// tracing.js - Initialize OpenTelemetry
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');
const { OTLPMetricExporter } = require('@opentelemetry/exporter-metrics-otlp-http');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');
const { PeriodicExportingMetricReader } = require('@opentelemetry/sdk-metrics');

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'express-api',
    [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0',
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.NODE_ENV || 'development',
  }),
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT || 'http://localhost:4318/v1/traces',
  }),
  metricReader: new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter({
      url: process.env.OTEL_EXPORTER_OTLP_METRICS_ENDPOINT || 'http://localhost:4318/v1/metrics',
    }),
  }),
  instrumentations: [
    getNodeAutoInstrumentations({
      '@opentelemetry/instrumentation-fs': {
        enabled: false, // Disable file system instrumentation if too verbose
      },
    }),
  ],
});

sdk.start();

process.on('SIGTERM', () => {
  sdk.shutdown()
    .then(() => console.log('Tracing terminated'))
    .catch((error) => console.log('Error terminating tracing', error))
    .finally(() => process.exit(0));
});

module.exports = sdk;

// app.js - Express application
require('./tracing'); // Must be first import

const express = require('express');
const opentelemetry = require('@opentelemetry/api');
const { trace, metrics, SpanStatusCode } = require('@opentelemetry/api');

const app = express();
app.use(express.json());

const tracer = trace.getTracer('express-api-tracer');
const meter = metrics.getMeter('express-api-meter');

// Custom metrics
const requestCounter = meter.createCounter('api.requests.total', {
  description: 'Total number of API requests',
});

const requestDuration = meter.createHistogram('api.request.duration', {
  description: 'API request duration',
  unit: 'ms',
});

// Middleware to add custom attributes to auto-instrumented spans
app.use((req, res, next) => {
  const span = trace.getActiveSpan();
  if (span) {
    span.setAttribute('user.agent', req.get('user-agent'));
    span.setAttribute('client.ip', req.ip);
  }
  next();
});

// GET /users - List users with pagination
app.get('/users', async (req, res) => {
  const startTime = Date.now();
  const span = tracer.startSpan('list-users');
  
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    
    span.setAttribute('pagination.page', page);
    span.setAttribute('pagination.limit', limit);

    const users = await getUsersFromDatabase(page, limit);
    
    span.setAttribute('users.count', users.length);
    span.setStatus({ code: SpanStatusCode.OK });
    
    requestCounter.add(1, { 
      method: 'GET', 
      route: '/users', 
      status: 200 
    });
    requestDuration.record(Date.now() - startTime, {
      method: 'GET',
      route: '/users',
    });
    
    res.json({ users, page, limit });
  } catch (error) {
    span.recordException(error);
    span.setStatus({ 
      code: SpanStatusCode.ERROR, 
      message: error.message 
    });
    
    requestCounter.add(1, { 
      method: 'GET', 
      route: '/users', 
      status: 500 
    });
    
    res.status(500).json({ error: 'Internal server error' });
  } finally {
    span.end();
  }
});

// POST /users - Create a new user
app.post('/users', async (req, res) => {
  const span = tracer.startSpan('create-user');
  
  try {
    const { name, email } = req.body;
    
    span.setAttribute('user.email', email);
    
    // Validate input - using context to establish parent-child relationship
    const ctx = opentelemetry.trace.setSpan(opentelemetry.context.active(), span);
    const validationSpan = tracer.startSpan('validate-user-input', {}, ctx);
    
    if (!name || !email) {
      validationSpan.setAttribute('validation.failed', true);
      validationSpan.end();
      
      span.setStatus({ 
        code: SpanStatusCode.ERROR, 
        message: 'Invalid input' 
      });
      
      return res.status(400).json({ error: 'Name and email required' });
    }
    validationSpan.end();
    
    // Create user in database
    const user = await createUserInDatabase({ name, email });
    
    span.setAttribute('user.id', user.id);
    span.setAttribute('user.created', true);
    span.setStatus({ code: SpanStatusCode.OK });
    
    requestCounter.add(1, { 
      method: 'POST', 
      route: '/users', 
      status: 201 
    });
    
    res.status(201).json(user);
  } catch (error) {
    span.recordException(error);
    span.setStatus({ code: SpanStatusCode.ERROR });
    
    requestCounter.add(1, { 
      method: 'POST', 
      route: '/users', 
      status: 500 
    });
    
    res.status(500).json({ error: error.message });
  } finally {
    span.end();
  }
});

async function getUsersFromDatabase(page, limit) {
  const span = tracer.startSpan('db.query.users');
  span.setAttribute('db.operation', 'SELECT');
  span.setAttribute('db.table', 'users');
  
  try {
    // Simulated database query
    const users = []; // Database query result
    span.setStatus({ code: SpanStatusCode.OK });
    return users;
  } finally {
    span.end();
  }
}

async function createUserInDatabase(userData) {
  const span = tracer.startSpan('db.insert.user');
  span.setAttribute('db.operation', 'INSERT');
  span.setAttribute('db.table', 'users');
  
  try {
    // Simulated database insert
    const user = { id: 1, ...userData };
    span.setStatus({ code: SpanStatusCode.OK });
    return user;
  } finally {
    span.end();
  }
}

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

## Example 2: React Application with User Interaction Tracing

```typescript
// tracing.ts - Browser instrumentation setup
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { ZoneContextManager } from '@opentelemetry/context-zone';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { DocumentLoadInstrumentation } from '@opentelemetry/instrumentation-document-load';
import { UserInteractionInstrumentation } from '@opentelemetry/instrumentation-user-interaction';
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

const provider = new WebTracerProvider({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'react-frontend',
    [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0',
  }),
});

const exporter = new OTLPTraceExporter({
  url: 'http://localhost:4318/v1/traces',
});

provider.addSpanProcessor(new BatchSpanProcessor(exporter, {
  maxQueueSize: 100,
  scheduledDelayMillis: 5000,
}));

provider.register({
  contextManager: new ZoneContextManager(),
});

registerInstrumentations({
  instrumentations: [
    new DocumentLoadInstrumentation(),
    new UserInteractionInstrumentation({
      eventNames: ['click', 'submit', 'keypress'],
    }),
    new FetchInstrumentation({
      propagateTraceHeaderCorsUrls: [
        /^https?:\/\/api\.example\.com\/.*/,
      ],
      clearTimingResources: true,
    }),
  ],
});

export default provider;

// App.tsx - React application
import React, { useEffect, useState } from 'react';
import { trace, SpanStatusCode } from '@opentelemetry/api';
import './tracing'; // Initialize tracing

const tracer = trace.getTracer('react-app');

interface User {
  id: number;
  name: string;
  email: string;
}

function UserList() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const span = tracer.startSpan('fetch-users-effect');
    span.setAttribute('component', 'UserList');

    setLoading(true);
    
    fetch('/api/users')
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setUsers(data.users);
        span.setAttribute('users.count', data.users.length);
        span.setStatus({ code: SpanStatusCode.OK });
      })
      .catch((err) => {
        setError(err.message);
        span.recordException(err);
        span.setStatus({ code: SpanStatusCode.ERROR });
      })
      .finally(() => {
        setLoading(false);
        span.end();
      });
  }, []);

  const handleDeleteUser = async (userId: number) => {
    const span = tracer.startSpan('delete-user-action', {
      attributes: {
        'user.id': userId,
        'action': 'delete',
      },
    });

    try {
      const response = await fetch(`/api/users/${userId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete user');
      }

      setUsers(users.filter(u => u.id !== userId));
      span.setAttribute('delete.success', true);
      span.setStatus({ code: SpanStatusCode.OK });
    } catch (err) {
      span.recordException(err as Error);
      span.setStatus({ code: SpanStatusCode.ERROR });
      alert('Failed to delete user');
    } finally {
      span.end();
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h1>Users</h1>
      <ul>
        {users.map(user => (
          <li key={user.id}>
            {user.name} ({user.email})
            <button onClick={() => handleDeleteUser(user.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default UserList;
```

## Example 3: Next.js with Server and Client Instrumentation

```typescript
// instrumentation.ts - Next.js 13+ instrumentation hook
export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    // Server-side instrumentation
    const { NodeSDK } = await import('@opentelemetry/sdk-node');
    const { getNodeAutoInstrumentations } = await import('@opentelemetry/auto-instrumentations-node');
    const { OTLPTraceExporter } = await import('@opentelemetry/exporter-trace-otlp-http');
    const { Resource } = await import('@opentelemetry/resources');
    const { SemanticResourceAttributes } = await import('@opentelemetry/semantic-conventions');

    const sdk = new NodeSDK({
      resource: new Resource({
        [SemanticResourceAttributes.SERVICE_NAME]: 'nextjs-app',
        [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.NODE_ENV,
      }),
      traceExporter: new OTLPTraceExporter({
        url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4318/v1/traces',
      }),
      instrumentations: [
        getNodeAutoInstrumentations({
          '@opentelemetry/instrumentation-fs': {
            enabled: false,
          },
        }),
      ],
    });

    sdk.start();

    process.on('SIGTERM', () => {
      sdk.shutdown().finally(() => process.exit(0));
    });
  }

  if (process.env.NEXT_RUNTIME === 'edge') {
    // Edge runtime instrumentation (limited support)
    console.log('Edge runtime detected - limited instrumentation available');
  }
}

// app/api/products/route.ts - API Route with tracing
import { trace, SpanStatusCode } from '@opentelemetry/api';
import { NextRequest, NextResponse } from 'next/server';

const tracer = trace.getTracer('nextjs-api');

export async function GET(request: NextRequest) {
  const span = tracer.startSpan('api.products.get', {
    attributes: {
      'http.method': 'GET',
      'http.route': '/api/products',
    },
  });

  try {
    const searchParams = request.nextUrl.searchParams;
    const category = searchParams.get('category');
    
    span.setAttribute('query.category', category || 'all');

    const products = await fetchProducts(category);
    
    span.setAttribute('products.count', products.length);
    span.setStatus({ code: SpanStatusCode.OK });

    return NextResponse.json({ products });
  } catch (error) {
    span.recordException(error as Error);
    span.setStatus({ code: SpanStatusCode.ERROR });
    
    return NextResponse.json(
      { error: 'Failed to fetch products' },
      { status: 500 }
    );
  } finally {
    span.end();
  }
}

async function fetchProducts(category: string | null) {
  const span = tracer.startSpan('db.query.products', {
    attributes: {
      'db.operation': 'SELECT',
      'db.table': 'products',
      'query.category': category || 'all',
    },
  });

  try {
    // Simulated database query
    const products = [];
    span.setStatus({ code: SpanStatusCode.OK });
    return products;
  } finally {
    span.end();
  }
}

// app/products/page.tsx - Server component with tracing
import { trace, SpanStatusCode } from '@opentelemetry/api';

const tracer = trace.getTracer('nextjs-pages');

async function ProductsPage({ searchParams }: { searchParams: { category?: string } }) {
  const span = tracer.startSpan('page.products.render', {
    attributes: {
      'page': 'products',
      'category': searchParams.category || 'all',
    },
  });

  try {
    const response = await fetch(
      `http://localhost:3000/api/products?category=${searchParams.category || ''}`,
      {
        next: { revalidate: 60 }, // ISR
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch products');
    }

    const data = await response.json();
    
    span.setAttribute('products.fetched', data.products.length);
    span.setStatus({ code: SpanStatusCode.OK });

    return (
      <div>
        <h1>Products</h1>
        <ProductList products={data.products} />
      </div>
    );
  } catch (error) {
    span.recordException(error as Error);
    span.setStatus({ code: SpanStatusCode.ERROR });
    return <div>Error loading products</div>;
  } finally {
    span.end();
  }
}

// components/ProductList.tsx - Client component
'use client';

import { trace, SpanStatusCode } from '@opentelemetry/api';
import { useState } from 'react';

const tracer = trace.getTracer('nextjs-components');

export function ProductList({ products }) {
  const [cart, setCart] = useState([]);

  const addToCart = (product) => {
    const span = tracer.startSpan('user.add-to-cart', {
      attributes: {
        'product.id': product.id,
        'product.name': product.name,
      },
    });

    try {
      setCart([...cart, product]);
      span.setAttribute('cart.size', cart.length + 1);
      span.setStatus({ code: SpanStatusCode.OK });
    } catch (error) {
      span.recordException(error);
      span.setStatus({ code: SpanStatusCode.ERROR });
    } finally {
      span.end();
    }
  };

  return (
    <div>
      {products.map(product => (
        <div key={product.id}>
          <h3>{product.name}</h3>
          <button onClick={() => addToCart(product)}>Add to Cart</button>
        </div>
      ))}
    </div>
  );
}
```

## Example 4: TypeScript Microservice with Database and HTTP Calls

```typescript
// tracing.ts - Instrumentation setup
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc';
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-grpc';
import { PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { ParentBasedSampler, TraceIdRatioBasedSampler } from '@opentelemetry/sdk-trace-base';

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'order-service',
    [SemanticResourceAttributes.SERVICE_VERSION]: process.env.SERVICE_VERSION || '1.0.0',
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.ENVIRONMENT || 'development',
  }),
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'localhost:4317',
  }),
  metricReader: new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter({
      url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'localhost:4317',
    }),
    exportIntervalMillis: 30000,
  }),
  sampler: new ParentBasedSampler({
    root: new TraceIdRatioBasedSampler(0.1), // Sample 10% in production
  }),
  instrumentations: [
    getNodeAutoInstrumentations({
      '@opentelemetry/instrumentation-pg': {
        enhancedDatabaseReporting: true,
      },
      '@opentelemetry/instrumentation-http': {
        ignoreIncomingPaths: ['/health', '/metrics'],
      },
    }),
  ],
});

sdk.start();

export default sdk;

// services/OrderService.ts - Business logic with instrumentation
import { trace, context, SpanStatusCode, Span } from '@opentelemetry/api';
import axios from 'axios';
import { Pool } from 'pg';

const tracer = trace.getTracer('order-service');
const pool = new Pool({
  host: process.env.DB_HOST,
  database: process.env.DB_NAME,
});

interface Order {
  id: string;
  userId: string;
  items: OrderItem[];
  total: number;
  status: string;
}

interface OrderItem {
  productId: string;
  quantity: number;
  price: number;
}

export class OrderService {
  async createOrder(userId: string, items: OrderItem[]): Promise<Order> {
    const span = tracer.startSpan('OrderService.createOrder', {
      attributes: {
        'user.id': userId,
        'order.items.count': items.length,
      },
    });

    try {
      // Validate user exists
      const userValid = await this.validateUser(userId);
      if (!userValid) {
        throw new Error('Invalid user');
      }

      // Check inventory
      const inventoryCheck = await this.checkInventory(items);
      span.setAttribute('inventory.available', inventoryCheck.available);

      if (!inventoryCheck.available) {
        throw new Error('Insufficient inventory');
      }

      // Calculate total
      const total = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
      span.setAttribute('order.total', total);

      // Create order in database
      const order = await this.saveOrder(userId, items, total);
      span.setAttribute('order.id', order.id);

      // Notify payment service
      await this.notifyPaymentService(order);

      span.setStatus({ code: SpanStatusCode.OK });
      return order;
    } catch (error) {
      span.recordException(error as Error);
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: (error as Error).message,
      });
      throw error;
    } finally {
      span.end();
    }
  }

  private async validateUser(userId: string): Promise<boolean> {
    const span = tracer.startSpan('OrderService.validateUser', {
      attributes: {
        'user.id': userId,
      },
    });

    try {
      const response = await axios.get(`http://user-service/api/users/${userId}`, {
        timeout: 5000,
      });

      span.setAttribute('user.found', response.status === 200);
      span.setStatus({ code: SpanStatusCode.OK });
      return response.status === 200;
    } catch (error) {
      span.recordException(error as Error);
      span.setStatus({ code: SpanStatusCode.ERROR });
      return false;
    } finally {
      span.end();
    }
  }

  private async checkInventory(items: OrderItem[]): Promise<{ available: boolean }> {
    const span = tracer.startSpan('OrderService.checkInventory', {
      attributes: {
        'items.count': items.length,
      },
    });

    try {
      const response = await axios.post('http://inventory-service/api/check', {
        items: items.map(i => ({ productId: i.productId, quantity: i.quantity })),
      });

      const available = response.data.available;
      span.setAttribute('inventory.available', available);
      span.setStatus({ code: SpanStatusCode.OK });

      return { available };
    } catch (error) {
      span.recordException(error as Error);
      span.setStatus({ code: SpanStatusCode.ERROR });
      throw error;
    } finally {
      span.end();
    }
  }

  private async saveOrder(userId: string, items: OrderItem[], total: number): Promise<Order> {
    const span = tracer.startSpan('OrderService.saveOrder', {
      attributes: {
        'db.operation': 'INSERT',
        'db.table': 'orders',
      },
    });

    const client = await pool.connect();

    try {
      await client.query('BEGIN');

      // Insert order
      const orderResult = await client.query(
        'INSERT INTO orders (user_id, total, status, created_at) VALUES ($1, $2, $3, NOW()) RETURNING id',
        [userId, total, 'pending']
      );

      const orderId = orderResult.rows[0].id;
      span.setAttribute('order.id', orderId);

      // Insert order items
      for (const item of items) {
        await client.query(
          'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES ($1, $2, $3, $4)',
          [orderId, item.productId, item.quantity, item.price]
        );
      }

      await client.query('COMMIT');

      span.setStatus({ code: SpanStatusCode.OK });

      return {
        id: orderId,
        userId,
        items,
        total,
        status: 'pending',
      };
    } catch (error) {
      await client.query('ROLLBACK');
      span.recordException(error as Error);
      span.setStatus({ code: SpanStatusCode.ERROR });
      throw error;
    } finally {
      client.release();
      span.end();
    }
  }

  private async notifyPaymentService(order: Order): Promise<void> {
    const span = tracer.startSpan('OrderService.notifyPaymentService', {
      attributes: {
        'order.id': order.id,
        'order.total': order.total,
      },
    });

    try {
      await axios.post('http://payment-service/api/payments', {
        orderId: order.id,
        amount: order.total,
        userId: order.userId,
      });

      span.setStatus({ code: SpanStatusCode.OK });
    } catch (error) {
      // Log error but don't fail order creation
      span.recordException(error as Error);
      span.setStatus({ code: SpanStatusCode.ERROR });
      console.error('Failed to notify payment service', error);
    } finally {
      span.end();
    }
  }
}
```

## Example 5: Custom Instrumentation Hook for Async Operations

```typescript
// hooks/useTracedAsync.ts - Reusable tracing hook
import { trace, Span, SpanStatusCode } from '@opentelemetry/api';
import { useCallback, useRef } from 'react';

const tracer = trace.getTracer('custom-hooks');

interface TracedAsyncOptions {
  operationName: string;
  attributes?: Record<string, any>;
  onSuccess?: (result: any, span: Span) => void;
  onError?: (error: Error, span: Span) => void;
}

export function useTracedAsync<T extends (...args: any[]) => Promise<any>>(
  asyncFunction: T,
  options: TracedAsyncOptions
): T {
  const spanRef = useRef<Span | null>(null);

  const tracedFunction = useCallback(
    async (...args: Parameters<T>): Promise<ReturnType<T>> => {
      const span = tracer.startSpan(options.operationName, {
        attributes: options.attributes,
      });
      spanRef.current = span;

      try {
        const result = await asyncFunction(...args);
        
        if (options.onSuccess) {
          options.onSuccess(result, span);
        }
        
        span.setStatus({ code: SpanStatusCode.OK });
        return result;
      } catch (error) {
        span.recordException(error as Error);
        span.setStatus({ 
          code: SpanStatusCode.ERROR,
          message: (error as Error).message,
        });
        
        if (options.onError) {
          options.onError(error as Error, span);
        }
        
        throw error;
      } finally {
        span.end();
        spanRef.current = null;
      }
    },
    [asyncFunction, options]
  ) as T;

  return tracedFunction;
}

// Usage example
function UserDashboard() {
  const fetchUserData = async (userId: string) => {
    const response = await fetch(`/api/users/${userId}`);
    return response.json();
  };

  const tracedFetchUserData = useTracedAsync(fetchUserData, {
    operationName: 'fetch-user-dashboard-data',
    attributes: { component: 'UserDashboard' },
    onSuccess: (result, span) => {
      span.setAttribute('user.name', result.name);
      span.setAttribute('user.premium', result.isPremium);
    },
  });

  return (
    <button onClick={() => tracedFetchUserData('user-123')}>
      Load Dashboard
    </button>
  );
}
```

## Example 6: GraphQL Server with OpenTelemetry

```typescript
// server.ts - GraphQL server with instrumentation
import './tracing'; // Must be first

import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { trace, SpanStatusCode } from '@opentelemetry/api';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { GraphQLInstrumentation } from '@opentelemetry/instrumentation-graphql';

// Register GraphQL instrumentation
registerInstrumentations({
  instrumentations: [
    new GraphQLInstrumentation({
      mergeItems: true,
      allowValues: true,
    }),
  ],
});

const tracer = trace.getTracer('graphql-server');

const typeDefs = `#graphql
  type Book {
    id: ID!
    title: String!
    author: String!
  }

  type Query {
    books: [Book]
    book(id: ID!): Book
  }

  type Mutation {
    addBook(title: String!, author: String!): Book
  }
`;

const books = [
  { id: '1', title: 'The Awakening', author: 'Kate Chopin' },
  { id: '2', title: 'City of Glass', author: 'Paul Auster' },
];

const resolvers = {
  Query: {
    books: async () => {
      const span = tracer.startSpan('resolver.books');
      
      try {
        // Simulate database call
        await new Promise(resolve => setTimeout(resolve, 100));
        span.setAttribute('books.count', books.length);
        span.setStatus({ code: SpanStatusCode.OK });
        return books;
      } catch (error) {
        span.recordException(error as Error);
        span.setStatus({ code: SpanStatusCode.ERROR });
        throw error;
      } finally {
        span.end();
      }
    },
    book: async (_parent, args: { id: string }) => {
      const span = tracer.startSpan('resolver.book', {
        attributes: { 'book.id': args.id },
      });
      
      try {
        const book = books.find(b => b.id === args.id);
        span.setAttribute('book.found', !!book);
        span.setStatus({ code: SpanStatusCode.OK });
        return book;
      } finally {
        span.end();
      }
    },
  },
  Mutation: {
    addBook: async (_parent, args: { title: string; author: string }) => {
      const span = tracer.startSpan('resolver.addBook', {
        attributes: {
          'book.title': args.title,
          'book.author': args.author,
        },
      });

      try {
        const newBook = {
          id: String(books.length + 1),
          title: args.title,
          author: args.author,
        };
        books.push(newBook);
        span.setAttribute('book.id', newBook.id);
        span.setStatus({ code: SpanStatusCode.OK });
        return newBook;
      } catch (error) {
        span.recordException(error as Error);
        span.setStatus({ code: SpanStatusCode.ERROR });
        throw error;
      } finally {
        span.end();
      }
    },
  },
};

const server = new ApolloServer({
  typeDefs,
  resolvers,
});

const { url } = await startStandaloneServer(server, {
  listen: { port: 4000 },
});

console.log(`🚀 Server ready at: ${url}`);
```

## Example 7: Custom Sampler for High-Value Traces

```typescript
// samplers/CustomSampler.ts
import { 
  Sampler, 
  SamplingDecision, 
  SamplingResult,
  Context,
  SpanKind,
  Attributes,
} from '@opentelemetry/sdk-trace-base';

export class BusinessValueSampler implements Sampler {
  private readonly defaultSampleRate: number;
  private readonly errorSampleRate: number;
  private readonly highValuePaths: Set<string>;

  constructor(options: {
    defaultSampleRate?: number;
    errorSampleRate?: number;
    highValuePaths?: string[];
  } = {}) {
    this.defaultSampleRate = options.defaultSampleRate || 0.01; // 1% default
    this.errorSampleRate = options.errorSampleRate || 1.0; // 100% for errors
    this.highValuePaths = new Set(options.highValuePaths || ['/checkout', '/payment']);
  }

  shouldSample(
    context: Context,
    traceId: string,
    spanName: string,
    spanKind: SpanKind,
    attributes: Attributes,
  ): SamplingResult {
    // Always sample errors
    const statusCode = attributes['http.status_code'] as number;
    if (statusCode && statusCode >= 400) {
      return {
        decision: SamplingDecision.RECORD_AND_SAMPLED,
        attributes: { 'sampler.type': 'error' },
      };
    }

    // Always sample high-value business paths
    const httpRoute = attributes['http.route'] as string;
    if (httpRoute && this.highValuePaths.has(httpRoute)) {
      return {
        decision: SamplingDecision.RECORD_AND_SAMPLED,
        attributes: { 'sampler.type': 'high-value' },
      };
    }

    // Sample VIP users at higher rate
    const userTier = attributes['user.tier'] as string;
    if (userTier === 'premium' || userTier === 'vip') {
      if (Math.random() < 0.5) { // 50% for VIP users
        return {
          decision: SamplingDecision.RECORD_AND_SAMPLED,
          attributes: { 'sampler.type': 'vip-user' },
        };
      }
    }

    // Default sampling
    if (Math.random() < this.defaultSampleRate) {
      return {
        decision: SamplingDecision.RECORD_AND_SAMPLED,
        attributes: { 'sampler.type': 'random' },
      };
    }

    return {
      decision: SamplingDecision.NOT_RECORD,
    };
  }

  toString(): string {
    return 'BusinessValueSampler';
  }
}

// Usage in tracing.ts
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { BusinessValueSampler } from './samplers/CustomSampler';

const provider = new NodeTracerProvider({
  sampler: new BusinessValueSampler({
    defaultSampleRate: 0.01,
    errorSampleRate: 1.0,
    highValuePaths: ['/checkout', '/payment', '/api/orders'],
  }),
});
```

These examples demonstrate comprehensive instrumentation patterns for the JavaScript ecosystem, including Express.js, React, Next.js, GraphQL, TypeScript, and advanced patterns like custom samplers and reusable hooks.
