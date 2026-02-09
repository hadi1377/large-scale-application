// Stress Test - Test system limits
// Run: k6 run scenarios/stress.js

import { check, sleep } from 'k6';
import http from 'k6/http';
import { Rate } from 'k6/metrics';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';
import { config, getApiGatewayUrl } from '../config.js';
import { createTestUser } from '../utils/auth.js';
import { getProducts, createProduct } from '../utils/products.js';
import { createOrder, getOrders } from '../utils/orders.js';

export let options = {
  stages: [
    { duration: '2m', target: 20 },   // Ramp up to 20 users
    { duration: '5m', target: 20 },   // Stay at 20 users
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '5m', target: 50 },   // Stay at 50 users
    { duration: '2m', target: 100 },  // Ramp up to 100 users
    { duration: '5m', target: 100 },   // Stay at 100 users
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000', 'p(99)<5000'], // More lenient for stress test
    http_req_failed: ['rate<0.05'], // Allow up to 5% failures under stress
  },
};

const baseUrl = getApiGatewayUrl();
const errorRate = new Rate('errors');

export default function () {
  const userId = __VU;
  const { token } = createTestUser(baseUrl, userId);
  
  // Mix of operations to stress different services
  
  // Product browsing (read-heavy)
  let response = http.get(`${baseUrl}/api/product-service/products?limit=50`);
  if (!check(response, { 'products retrieved': (r) => r.status === 200 })) {
    errorRate.add(1);
  }
  sleep(0.5);

  // Get user info
  response = http.get(`${baseUrl}/api/user-service/me`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  check(response, { 'user info retrieved': (r) => r.status === 200 });
  sleep(0.5);

  // Create product (write operation)
  if (Math.random() < 0.2) {
    const product = createProduct(baseUrl, token, {
      name: `Stress Test Product ${Date.now()}-${userId}`,
      price: Math.random() * 100,
      stock: Math.floor(Math.random() * 1000),
    });
    sleep(0.5);
  }

  // Create order (complex operation)
  if (Math.random() < 0.15) {
    const productsResponse = http.get(`${baseUrl}/api/product-service/products?limit=10`);
    if (productsResponse.status === 200) {
      const products = productsResponse.json();
      if (products && products.length > 0) {
        const orderItems = products.slice(0, 3).map(p => ({
          product_id: p.id,
          quantity: Math.floor(Math.random() * 5) + 1,
          price: p.price
        }));
        
        const orderData = {
          items: orderItems,
          shipping_address: {
            street: `${userId} Test St`,
            city: 'Stress City',
            state: 'ST',
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
        check(response, { 'order created': (r) => r.status === 201 });
      }
    }
  }
  sleep(1);
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'k6-results.json': JSON.stringify(data, null, 2),
    'k6-summary.json': JSON.stringify({
      timestamp: new Date().toISOString(),
      test: 'stress',
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

