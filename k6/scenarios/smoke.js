// Smoke Test - Quick validation that the system works
// Run: k6 run scenarios/smoke.js

import { check, sleep } from 'k6';
import http from 'k6/http';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';
import { config, getApiGatewayUrl } from '../config.js';
import { registerUser, loginUser } from '../utils/auth.js';
import { getProducts } from '../utils/products.js';

export let options = {
  stages: [
    { duration: '30s', target: 1 }, // 1 user for 30 seconds
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'],
    http_req_failed: ['rate<0.05'],
  },
};

const baseUrl = getApiGatewayUrl();

export default function () {
  // Test API Gateway health
  let response = http.get(`${baseUrl}/health`);
  check(response, {
    'API Gateway is healthy': (r) => r.status === 200,
  });
  sleep(1);

  // Test user registration
  const email = `smoketest${Date.now()}@example.com`;
  registerUser(baseUrl, email, 'testpass123', 'Smoke Test User');
  sleep(1);

  // Test user login
  const token = loginUser(baseUrl, email, 'testpass123');
  sleep(1);

  // Test product listing
  getProducts(baseUrl);
  sleep(1);
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
  };
}

