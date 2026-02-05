// Authentication utilities for k6 tests
import http from 'k6/http';
import { check } from 'k6';

/**
 * Register a new user and return user data
 */
export function registerUser(baseUrl, email, password, fullName) {
  const response = http.post(`${baseUrl}/api/user-service/register`, JSON.stringify({
    email: email,
    password: password,
    full_name: fullName
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  check(response, {
    'registration successful': (r) => r.status === 201,
  });
  
  return response.json();
}

/**
 * Login a user and return access token
 */
export function loginUser(baseUrl, email, password) {
  const response = http.post(`${baseUrl}/api/user-service/login`, JSON.stringify({
    email: email,
    password: password
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  check(response, {
    'login successful': (r) => r.status === 200,
    'token received': (r) => r.json('access_token') !== undefined,
  });
  
  return response.json().access_token;
}

/**
 * Get authenticated headers with Bearer token
 */
export function getAuthHeaders(token) {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };
}

/**
 * Create a test user and return token
 * Useful for tests that need authentication
 */
export function createTestUser(baseUrl, userId) {
  const email = `testuser${userId}@example.com`;
  const password = 'testpassword123';
  const fullName = `Test User ${userId}`;
  
  // Try to register (might fail if user exists, that's ok)
  registerUser(baseUrl, email, password, fullName);
  
  // Login to get token
  const token = loginUser(baseUrl, email, password);
  
  return { email, password, fullName, token };
}


