// Order service utilities for k6 tests
import http from 'k6/http';
import { check } from 'k6';

/**
 * Create an order
 */
export function createOrder(baseUrl, token, orderData) {
  const response = http.post(
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
  
  return response.json();
}

/**
 * Build query string from params object
 */
function buildQueryString(params) {
  const parts = [];
  for (const key in params) {
    if (params[key] !== null && params[key] !== undefined) {
      parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`);
    }
  }
  return parts.length > 0 ? '?' + parts.join('&') : '';
}

/**
 * Get all orders for the authenticated user
 */
export function getOrders(baseUrl, token, params = {}) {
  const queryString = buildQueryString(params);
  const url = `${baseUrl}/api/order-service/orders${queryString}`;
  
  const response = http.get(url, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  
  check(response, {
    'orders retrieved': (r) => r.status === 200,
  });
  
  return response.json();
}

/**
 * Get a single order by ID
 */
export function getOrder(baseUrl, token, orderId) {
  const response = http.get(
    `${baseUrl}/api/order-service/orders/${orderId}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );
  
  check(response, {
    'order retrieved': (r) => r.status === 200,
  });
  
  return response.json();
}

/**
 * Update an order status
 */
export function updateOrder(baseUrl, token, orderId, status) {
  const response = http.put(
    `${baseUrl}/api/order-service/orders/${orderId}`,
    JSON.stringify({ status: status }),
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    }
  );
  
  check(response, {
    'order updated': (r) => r.status === 200,
  });
  
  return response.json();
}


