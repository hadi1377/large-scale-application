// Product service utilities for k6 tests
import http from 'k6/http';
import { check } from 'k6';

/**
 * Create a test product
 */
export function createProduct(baseUrl, token, productData = {}) {
  const defaultProduct = {
    name: `Test Product ${Date.now()}`,
    description: 'A test product for load testing',
    price: 29.99,
    stock: 100,
    category: 'electronics',
    ...productData
  };
  
  const response = http.post(
    `${baseUrl}/api/product-service/products`,
    JSON.stringify(defaultProduct),
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    }
  );
  
  check(response, {
    'product created': (r) => r.status === 201,
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
 * Get all products with optional filters
 */
export function getProducts(baseUrl, params = {}) {
  const queryString = buildQueryString(params);
  const url = `${baseUrl}/api/product-service/products${queryString}`;
  
  const response = http.get(url);
  
  check(response, {
    'products retrieved': (r) => r.status === 200,
  });
  
  return response.json();
}

/**
 * Get a single product by ID
 */
export function getProduct(baseUrl, productId) {
  const response = http.get(`${baseUrl}/api/product-service/products/${productId}`);
  
  check(response, {
    'product retrieved': (r) => r.status === 200,
  });
  
  return response.json();
}

/**
 * Update a product
 */
export function updateProduct(baseUrl, token, productId, updateData) {
  const response = http.put(
    `${baseUrl}/api/product-service/products/${productId}`,
    JSON.stringify(updateData),
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    }
  );
  
  check(response, {
    'product updated': (r) => r.status === 200,
  });
  
  return response.json();
}

/**
 * Delete a product
 */
export function deleteProduct(baseUrl, token, productId) {
  const response = http.del(
    `${baseUrl}/api/product-service/products/${productId}`,
    null,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );
  
  check(response, {
    'product deleted': (r) => r.status === 204,
  });
  
  return response;
}


