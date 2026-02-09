# Prometheus Monitoring Setup

This document describes the Prometheus monitoring setup for the microservices application.

## Overview

All services have been instrumented with Prometheus metrics using `prometheus-fastapi-instrumentator`. This automatically exposes metrics at the `/metrics` endpoint for each service.

## Metrics Exposed

Each service automatically exposes the following metrics:

- **http_requests_total**: Total number of HTTP requests
- **http_request_duration_seconds**: HTTP request duration in seconds
- **http_request_size_bytes**: HTTP request size in bytes
- **http_response_size_bytes**: HTTP response size in bytes
- **http_requests_created**: Timestamp of request creation

All metrics are labeled with:
- `method`: HTTP method (GET, POST, etc.)
- `endpoint`: API endpoint path
- `status_code`: HTTP status code

## Local Development (Docker Compose)

### Accessing Metrics

1. **Prometheus UI**: http://localhost:13260
   - View all collected metrics
   - Query metrics using PromQL
   - Create graphs and alerts

2. **Grafana UI**: http://localhost:13261
   - Username: `admin`
   - Password: `admin`
   - Pre-configured with Prometheus datasource

3. **Service Metrics Endpoints**:
   - API Gateway: http://localhost:13230/metrics
   - User Service: http://localhost:13231/metrics
   - Product Service: http://localhost:13232/metrics
   - Order Service: http://localhost:13233/metrics
   - Payment Service: http://localhost:13234/metrics
   - Notification Service: http://localhost:13235/metrics

### Starting Monitoring Stack

```bash
docker-compose up -d prometheus grafana
```

Or start everything:
```bash
docker-compose up -d
```

## Kubernetes Deployment

### Deploy Prometheus and Grafana

```bash
# Apply Prometheus configuration
kubectl apply -f k8s/monitoring/prometheus-config.yaml

# Deploy Prometheus
kubectl apply -f k8s/monitoring/prometheus-deployment.yaml

# Deploy Grafana
kubectl apply -f k8s/monitoring/grafana-deployment.yaml
```

### Accessing in Kubernetes

1. **Port Forward Prometheus**:
   ```bash
   kubectl port-forward -n microservices svc/prometheus 9090:9090
   ```
   Then access: http://localhost:9090

2. **Port Forward Grafana**:
   ```bash
   kubectl port-forward -n microservices svc/grafana 3000:3000
   ```
   Then access: http://localhost:3000
   - Username: `admin`
   - Password: `admin` (change in production!)

3. **Service Metrics** (from within cluster):
   - API Gateway: `http://api-gateway:8000/metrics`
   - User Service: `http://user-service:8000/metrics`
   - Product Service: `http://product-service:8000/metrics`
   - Order Service: `http://order-service:8000/metrics`
   - Payment Service: `http://payment-service:8000/metrics`
   - Notification Service: `http://notification-service:8000/metrics`

### Ingress Configuration (Optional)

To expose Prometheus and Grafana via Ingress, add to your ingress configuration:

```yaml
- host: prometheus.yourdomain.com
  http:
    paths:
    - path: /
      pathType: Prefix
      backend:
        service:
          name: prometheus
          port:
            number: 9090

- host: grafana.yourdomain.com
  http:
    paths:
    - path: /
      pathType: Prefix
      backend:
        service:
          name: grafana
          port:
            number: 3000
```

## Example PromQL Queries

### Request Rate
```
rate(http_requests_total[5m])
```

### Request Rate by Service
```
sum(rate(http_requests_total[5m])) by (service)
```

### Error Rate
```
sum(rate(http_requests_total{status_code=~"5.."}[5m])) by (service)
```

### Average Response Time
```
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

### 95th Percentile Response Time
```
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Requests per Endpoint
```
sum(rate(http_requests_total[5m])) by (endpoint, method)
```

## Grafana Dashboards

### Creating a Dashboard

1. Log into Grafana
2. Go to **Dashboards** → **New Dashboard**
3. Add a new panel
4. Select **Prometheus** as the data source
5. Use PromQL queries to visualize metrics

### Recommended Dashboards

1. **Service Overview**:
   - Request rate per service
   - Error rate per service
   - Response time percentiles

2. **Endpoint Performance**:
   - Top endpoints by request count
   - Slowest endpoints
   - Error rate by endpoint

3. **System Health**:
   - Service availability
   - Request success rate
   - Average response times

## Alerting (Future Enhancement)

You can set up alerts in Prometheus for:
- High error rates
- Slow response times
- Service unavailability
- Unusual traffic patterns

Example alert rule:
```yaml
groups:
- name: service_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.1
    for: 5m
    annotations:
      summary: "High error rate detected"
```

## Troubleshooting

### Metrics Not Appearing

1. Check if services are running:
   ```bash
   docker-compose ps
   # or
   kubectl get pods -n microservices
   ```

2. Verify metrics endpoint is accessible:
   ```bash
   curl http://localhost:13230/metrics
   ```

3. Check Prometheus targets:
   - Go to Prometheus UI → Status → Targets
   - All targets should be "UP"

### Prometheus Can't Scrape Services

1. Verify service names in `prometheus.yml` match Docker Compose service names
2. Check network connectivity (services must be on same Docker network)
3. Verify services expose `/metrics` endpoint

### Grafana Can't Connect to Prometheus

1. Check Prometheus service is running
2. Verify datasource URL: `http://prometheus:9090` (for Docker Compose)
3. For Kubernetes: `http://prometheus.microservices.svc.cluster.local:9090`

## Security Considerations

⚠️ **Important for Production**:

1. **Change Grafana default password**:
   - Update `k8s/monitoring/grafana-deployment.yaml` secret
   - Use a strong password

2. **Secure Prometheus**:
   - Add authentication/authorization
   - Use TLS for connections
   - Restrict network access

3. **Secure Metrics Endpoints**:
   - Consider adding authentication to `/metrics` endpoints
   - Use network policies to restrict access

4. **Data Retention**:
   - Adjust retention period based on storage capacity
   - Current: 30 days (configurable in deployment)

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus FastAPI Instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator)




