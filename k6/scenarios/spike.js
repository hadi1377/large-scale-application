// Spike Test - Sudden traffic spikes
// Run: k6 run scenarios/spike.js

import { check, sleep } from 'k6';
import http from 'k6/http';
import { Rate } from 'k6/metrics';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';
import { config, getApiGatewayUrl } from '../config.js';
import { createTestUser } from '../utils/auth.js';
import { getProducts } from '../utils/products.js';

export let options = {
  stages: [
    { duration: '1m', target: 10 },   // Normal load
    { duration: '30s', target: 200 },  // Sudden spike to 200 users
    { duration: '1m', target: 200 },  // Stay at spike
    { duration: '30s', target: 10 },  // Back to normal
    { duration: '1m', target: 10 },   // Normal load
    { duration: '30s', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<3000'], // More lenient for spikes
    http_req_failed: ['rate<0.1'],     // Allow up to 10% failures during spikes
  },
};

const baseUrl = getApiGatewayUrl();
const errorRate = new Rate('errors');

export default function () {
  const userId = __VU;
  const { token } = createTestUser(baseUrl, userId);
  
  // Simple operations that can handle spikes
  // Focus on read operations which are more resilient
  
  // Health check
  let response = http.get(`${baseUrl}/health`);
  check(response, { 'health check passed': (r) => r.status === 200 });
  
  // Browse products
  response = http.get(`${baseUrl}/api/product-service/products?limit=20`);
  if (!check(response, { 'products retrieved': (r) => r.status === 200 })) {
    errorRate.add(1);
  }
  
  // Get user orders
  response = http.get(`${baseUrl}/api/order-service/orders`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  check(response, { 'orders retrieved': (r) => r.status === 200 });
  
  sleep(1);
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
  };
}

