# k6 Load Testing

This directory contains k6 load testing scripts for the microservices application.

## Prerequisites

Install k6:
- **Windows**: Download from [k6.io](https://k6.io/docs/getting-started/installation/) or use `choco install k6`
- **macOS**: `brew install k6`
- **Linux**: Follow [official installation guide](https://k6.io/docs/getting-started/installation/)

## Quick Start

### 1. Start Your Application

Make sure your application is running. For local testing:
```bash
# If using Kubernetes
kubectl port-forward -n microservices svc/api-gateway 8050:8000

# Or if using docker-compose
# The API Gateway should be accessible at http://localhost:8050
```

### 2. Run Tests

#### Smoke Test (Quick validation)
```bash
k6 run scenarios/smoke.js
```

#### Load Test (Normal expected load)
```bash
k6 run scenarios/load.js
```

#### Stress Test (System limits)
```bash
k6 run scenarios/stress.js
```

#### Spike Test (Sudden traffic spikes)
```bash
k6 run scenarios/spike.js
```

#### End-to-End Test (Complete user journey)
```bash
k6 run scenarios/e2e.js
```

### 3. Customize Base URL

Set a custom base URL via environment variable:
```bash
# Windows PowerShell
$env:BASE_URL="http://your-api-gateway-url:port"; k6 run scenarios/load.js

# Linux/macOS
BASE_URL=http://your-api-gateway-url:port k6 run scenarios/load.js
```

## Test Scenarios

### Smoke Test (`scenarios/smoke.js`)
- **Purpose**: Quick validation that the system works
- **Duration**: ~30 seconds
- **Users**: 1
- **Use Case**: Pre-deployment validation, quick health check

### Load Test (`scenarios/load.js`)
- **Purpose**: Test normal expected load
- **Duration**: ~9 minutes
- **Users**: Ramp up to 10, maintain, then ramp down
- **Use Case**: Validate system performance under normal conditions

### Stress Test (`scenarios/stress.js`)
- **Purpose**: Find system limits and breaking points
- **Duration**: ~23 minutes
- **Users**: Gradually increase from 20 to 100 users
- **Use Case**: Capacity planning, finding bottlenecks

### Spike Test (`scenarios/spike.js`)
- **Purpose**: Test system behavior under sudden traffic spikes
- **Duration**: ~4 minutes
- **Users**: Sudden spike from 10 to 200 users
- **Use Case**: Black Friday scenarios, viral traffic

### End-to-End Test (`scenarios/e2e.js`)
- **Purpose**: Complete user journey validation
- **Duration**: ~5 minutes
- **Users**: 5 concurrent users
- **Use Case**: Integration testing, user flow validation

## Test Structure

```
k6/
├── config.js              # Shared configuration
├── scenarios/              # Test scenarios
│   ├── smoke.js           # Smoke test
│   ├── load.js            # Load test
│   ├── stress.js          # Stress test
│   ├── spike.js           # Spike test
│   └── e2e.js             # End-to-end test
├── utils/                 # Utility functions
│   ├── auth.js            # Authentication helpers
│   ├── products.js        # Product service helpers
│   └── orders.js          # Order service helpers
└── README.md              # This file
```

## Understanding Results

k6 provides comprehensive metrics:

### Key Metrics

- **http_req_duration**: Request duration (p95, p99 percentiles)
- **http_req_failed**: Failed request rate
- **http_reqs**: Total requests per second
- **iterations**: Completed test iterations
- **vus**: Virtual users (concurrent)

### Thresholds

Each test defines thresholds that must be met:
- **http_req_duration**: Response time limits
- **http_req_failed**: Maximum failure rate
- **http_reqs**: Minimum requests per second

If thresholds are not met, the test will be marked as failed.

## Customizing Tests

### Modify User Count

Edit the `stages` in the test file:
```javascript
stages: [
  { duration: '2m', target: 20 },  // 20 users for 2 minutes
  { duration: '5m', target: 20 },  // Stay at 20 for 5 minutes
  { duration: '2m', target: 0 },   // Ramp down
],
```

### Adjust Thresholds

Modify the `thresholds` section:
```javascript
thresholds: {
  http_req_duration: ['p(95)<500'],  // 95% of requests < 500ms
  http_req_failed: ['rate<0.01'],    // Less than 1% failures
},
```

### Add Custom Metrics

```javascript
import { Rate, Trend } from 'k6/metrics';

const customErrorRate = new Rate('custom_errors');
const customDuration = new Trend('custom_duration');

// Use in your test
customErrorRate.add(1);
customDuration.add(response.timings.duration);
```

## CI/CD Integration

### GitHub Actions Example

Add to `.github/workflows/load-test.yml`:

```yaml
name: Load Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install k6
        run: |
          sudo gpg -k
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D9B
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6
      - name: Run smoke test
        run: |
          k6 run k6/scenarios/smoke.js --env BASE_URL=${{ secrets.API_GATEWAY_URL }}
```

## Best Practices

1. **Start Small**: Begin with smoke tests, then move to load tests
2. **Monitor Resources**: Watch CPU, memory, and database during tests
3. **Test Realistic Scenarios**: Model actual user behavior
4. **Run Regularly**: Include load tests in CI/CD pipeline
5. **Document Results**: Keep track of performance trends over time
6. **Test in Production-like Environment**: Use staging environment that mirrors production

## Troubleshooting

### Connection Refused
- Ensure the API Gateway is running and accessible
- Check the BASE_URL environment variable
- Verify port forwarding (if using Kubernetes)

### High Failure Rate
- Check if services are running and healthy
- Verify database connections
- Check service logs for errors
- Reduce load (fewer users) and retry

### Slow Response Times
- Check database performance
- Monitor service resource usage
- Review service logs for bottlenecks
- Consider scaling services

## Advanced Usage

### Running Multiple Scenarios

Create a script to run multiple tests:
```bash
#!/bin/bash
k6 run scenarios/smoke.js
k6 run scenarios/load.js
```

### Custom Output Formats

Export results to JSON:
```bash
k6 run --out json=results.json scenarios/load.js
```

### Cloud Execution

Use k6 Cloud for distributed load testing:
```bash
k6 cloud scenarios/load.js
```

## Resources

- [k6 Documentation](https://k6.io/docs/)
- [k6 JavaScript API](https://k6.io/docs/javascript-api/)
- [k6 Metrics](https://k6.io/docs/using-k6/metrics/)
- [k6 Thresholds](https://k6.io/docs/using-k6/thresholds/)




