// End-to-End Test - Complete user journey
// Run: k6 run scenarios/e2e.js

import { check, sleep } from 'k6';
import http from 'k6/http';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';
import { config, getApiGatewayUrl } from '../config.js';
import { registerUser, loginUser } from '../utils/auth.js';
import { getProducts, getProduct } from '../utils/products.js';
import { createOrder, getOrder, getOrders } from '../utils/orders.js';

export let options = {
  stages: [
    { duration: '1m', target: 5 },   // 5 concurrent users
    { duration: '3m', target: 5 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate<0.02'],
  },
};

const baseUrl = getApiGatewayUrl();

export default function () {
  const userId = __VU;
  const timestamp = Date.now();
  
  // Step 1: Register a new user
  const email = `e2euser${userId}-${timestamp}@example.com`;
  const password = 'e2epassword123';
  const fullName = `E2E User ${userId}`;
  
  let response = http.post(`${baseUrl}/api/user-service/register`, JSON.stringify({
    email: email,
    password: password,
    full_name: fullName
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  check(response, {
    'user registered': (r) => r.status === 201,
  });
  sleep(1);

  // Step 2: Login
  response = http.post(`${baseUrl}/api/user-service/login`, JSON.stringify({
    email: email,
    password: password
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  check(response, {
    'login successful': (r) => r.status === 200,
  });
  
  const token = response.json().access_token;
  const authHeaders = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };
  sleep(1);

  // Step 3: Get user profile
  response = http.get(`${baseUrl}/api/user-service/me`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  check(response, {
    'profile retrieved': (r) => r.status === 200,
    'correct email': (r) => r.json('email') === email,
  });
  sleep(1);

  // Step 4: Browse products
  response = http.get(`${baseUrl}/api/product-service/products?limit=10`);
  check(response, {
    'products listed': (r) => r.status === 200,
  });
  
  const products = response.json();
  check(products, {
    'products array returned': (p) => Array.isArray(p),
  });
  sleep(1);

  // Step 5: View a specific product
  if (products && products.length > 0) {
    const productId = products[0].id;
    response = http.get(`${baseUrl}/api/product-service/products/${productId}`);
    check(response, {
      'product details retrieved': (r) => r.status === 200,
      'product has id': (r) => r.json('id') === productId,
    });
    sleep(1);

    // Step 6: Create an order
    const orderItems = [{
      product_id: productId,
      quantity: 2,
      price: products[0].price
    }];
    
    const orderData = {
      items: orderItems,
      shipping_address: {
        street: '123 E2E Test St',
        city: 'E2E City',
        state: 'E2',
        zip_code: '12345',
        country: 'US'
      }
    };
    
    response = http.post(
      `${baseUrl}/api/order-service/orders`,
      JSON.stringify(orderData),
      { headers: authHeaders }
    );
    
    check(response, {
      'order created': (r) => r.status === 201,
    });
    
    const order = response.json();
    const orderId = order.id;
    sleep(1);

    // Step 7: Get order details
    response = http.get(
      `${baseUrl}/api/order-service/orders/${orderId}`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    check(response, {
      'order retrieved': (r) => r.status === 200,
      'order has correct id': (r) => r.json('id') === orderId,
    });
    sleep(1);

    // Step 8: List all user orders
    response = http.get(
      `${baseUrl}/api/order-service/orders`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    check(response, {
      'orders listed': (r) => r.status === 200,
    });
    sleep(1);
  }
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'k6-results.json': JSON.stringify(data, null, 2),
    'k6-summary.json': JSON.stringify({
      timestamp: new Date().toISOString(),
      test: 'e2e',
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

