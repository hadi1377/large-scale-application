// k6 Configuration
// This file contains shared configuration for all k6 tests

export const config = {
  // Base URL - can be overridden via environment variable
  baseUrl: __ENV.BASE_URL || 'http://localhost:8050',
  
  // Test thresholds
  thresholds: {
    // HTTP-specific thresholds
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% of requests < 500ms, 99% < 1s
    http_req_failed: ['rate<0.01'], // Less than 1% of requests should fail
    http_reqs: ['rate>10'], // More than 10 requests per second
    
    // Iteration thresholds
    iteration_duration: ['p(95)<2000'], // 95% of iterations < 2s
    
    // Data thresholds
    data_received: ['rate>1000'], // More than 1KB/s
    data_sent: ['rate>500'], // More than 500B/s
  },
  
  // Summary time unit
  summaryTimeUnit: 'ms',
};

// Helper function to get service URL
export function getServiceUrl(serviceName) {
  return `${config.baseUrl}/api/${serviceName}`;
}

// Helper function to get API Gateway URL
export function getApiGatewayUrl() {
  return config.baseUrl;
}


