// Load Test - Normal expected load
// Run: k6 run scenarios/load.js

import { check, sleep } from 'k6';
import http from 'k6/http';
import { Rate } from 'k6/metrics';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';
import { config, getApiGatewayUrl } from '../config.js';
import { createTestUser } from '../utils/auth.js';
import { getProducts, getProduct } from '../utils/products.js';
import { getOrders, createOrder } from '../utils/orders.js';

export let options = {
  stages: [
    { duration: '2m', target: 10 },  // Ramp up to 10 users over 2 minutes
    { duration: '5m', target: 10 },   // Stay at 10 users for 5 minutes
    { duration: '2m', target: 0 },   // Ramp down to 0 users over 2 minutes
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
  },
};

const baseUrl = getApiGatewayUrl();
const errorRate = new Rate('errors');

export default function () {
  const userId = __VU; // Virtual User ID
  const { token } = createTestUser(baseUrl, userId);
  
  // Browse products (most common operation)
  let response = http.get(`${baseUrl}/api/product-service/products?limit=20`);
  if (check(response, {
    'products retrieved': (r) => r.status === 200,
  })) {
    const products = response.json();
    if (products && products.length > 0) {
      // View a specific product
      const productId = products[0].id;
      http.get(`${baseUrl}/api/product-service/products/${productId}`);
    }
  } else {
    errorRate.add(1);
  }
  sleep(1);

  // Check user's orders
  response = http.get(`${baseUrl}/api/order-service/orders`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  check(response, {
    'orders retrieved': (r) => r.status === 200,
  });
  sleep(1);

  // Occasionally create an order (10% of iterations)
  if (Math.random() < 0.1) {
    const productsResponse = http.get(`${baseUrl}/api/product-service/products?limit=5`);
    if (productsResponse.status === 200) {
      const products = productsResponse.json();
      if (products && products.length > 0) {
        const orderItems = products.slice(0, 2).map(p => ({
          product_id: p.id,
          quantity: Math.floor(Math.random() * 3) + 1,
          price: p.price
        }));
        
        const orderData = {
          items: orderItems,
          shipping_address: {
            street: '123 Test St',
            city: 'Test City',
            state: 'TS',
            zip_code: '12345',
            country: 'US'
          }
        };
        
        response = http.post(
          `${baseUrl}/api/order-service/orders`,
          JSON.stringify(orderData),
          {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
          }
        );
        check(response, {
          'order created': (r) => r.status === 201,
        });
      }
    }
  }
  sleep(2);
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'k6-results.json': JSON.stringify(data, null, 2),
    'k6-summary.json': JSON.stringify({
      timestamp: new Date().toISOString(),
      test: 'load',
      metrics: {
        http_req_duration: {
          avg: data.metrics.http_req_duration?.values?.avg || 0,
          min: data.metrics.http_req_duration?.values?.min || 0,
          med: data.metrics.http_req_duration?.values?.med || 0,
          max: data.metrics.http_req_duration?.values?.max || 0,
          p95: data.metrics.http_req_duration?.values?.['p(95)'] || 0,
          p99: data.metrics.http_req_duration?.values?.['p(99)'] || 0,
        },
        http_req_failed: {
          rate: data.metrics.http_req_failed?.values?.rate || 0,
        },
        http_reqs: {
          rate: data.metrics.http_reqs?.values?.rate || 0,
          count: data.metrics.http_reqs?.values?.count || 0,
        },
        iterations: {
          count: data.metrics.iterations?.values?.count || 0,
          rate: data.metrics.iterations?.values?.rate || 0,
        },
        vus: {
          value: data.metrics.vus?.values?.value || 0,
          max: data.metrics.vus?.values?.max || 0,
        },
      },
      thresholds: data.root_group?.thresholds || {},
    }, null, 2),
  };
}

