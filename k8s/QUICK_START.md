# Quick Start Guide

Get your microservices running on Kubernetes in minutes!

## For Minikube (Local Development)

### 1. Start Minikube
```bash
minikube start --cpus=4 --memory=8192
minikube addons enable ingress
```

### 2. Build Images
```bash
cd k8s

# Linux/Mac
chmod +x build-images.sh deploy.sh undeploy.sh
./build-images.sh

# Windows PowerShell
.\build-images.ps1

# Note: The script will automatically navigate to the project root
# to find the service directories and build the images
```

### 3. Deploy
```bash
# Make sure you're still in the k8s directory
# cd k8s  (if you're not already there)

# Linux/Mac
./deploy.sh

# Windows PowerShell
.\deploy.ps1

# The script will automatically use the correct paths
# and deploy all services to the 'microservices' namespace
```

### 3.5. Deploy Monitoring (Optional but Recommended)
```bash
# Deploy Prometheus and Grafana
kubectl apply -f monitoring/prometheus-config.yaml
kubectl apply -f monitoring/prometheus-deployment.yaml
kubectl apply -f monitoring/grafana-deployment.yaml

# Wait for monitoring to be ready
kubectl wait --for=condition=ready pod -l app=prometheus -n microservices --timeout=120s
kubectl wait --for=condition=ready pod -l app=grafana -n microservices --timeout=120s
```

### 4. Access Services

#### Option A: Via Port Forward (Recommended for Minikube)
```bash
# API Gateway
kubectl port-forward -n microservices svc/api-gateway 8050:8000
# Visit: http://localhost:8050

# RabbitMQ Management UI
kubectl port-forward -n microservices svc/rabbitmq 15672:15672
# Visit: http://localhost:15672
# Login: rabbitmq_user / rabbitmq_password

# Mailpit Web UI
kubectl port-forward -n microservices svc/mailpit 8025:8025
# Visit: http://localhost:8025

# Prometheus (Monitoring)
kubectl port-forward -n microservices svc/prometheus 9090:9090
# Visit: http://localhost:9090

# Grafana (Dashboards)
kubectl port-forward -n microservices svc/grafana 3000:3000
# Visit: http://localhost:3000
# Login: admin / admin
```

#### Option B: Via Ingress
```bash
# Get Minikube IP
minikube ip

# Add to hosts file (Windows: C:\Windows\System32\drivers\etc\hosts)
# <minikube-ip>  microservices.local

# Then access:
# - API Gateway: http://microservices.local/
# - RabbitMQ: http://microservices.local/rabbitmq
# - Mailpit: http://microservices.local/mailpit
```

**Done!** 🎉

---

## For Cloud (GKE, EKS, AKS)

### 1. Build & Push Images
```bash
# Tag for your registry
docker tag api-gateway:latest <your-registry>/api-gateway:latest
docker push <your-registry>/api-gateway:latest
# Repeat for all services...
```

### 2. Update Image URLs
Edit all files in `services/` directory and update:
```yaml
image: <your-registry>/user-service:latest
```

### 3. Install Ingress Controller
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
```

### 4. Deploy
```bash
cd k8s
./deploy.sh  # or .\deploy.ps1 on Windows
```

### 5. Get URL
```bash
kubectl get ingress -n microservices
# Use the external IP or hostname
```

**Done!** 🎉

---

## Common Commands

### Check Status
```bash
kubectl get all -n microservices
```

### View Logs
```bash
kubectl logs -f deployment/api-gateway -n microservices
```

### Access Services
```bash
# API Gateway
kubectl port-forward -n microservices svc/api-gateway 8000:8000

# RabbitMQ UI
kubectl port-forward -n microservices svc/rabbitmq 15672:15672

# Mailpit UI
kubectl port-forward -n microservices svc/mailpit 8025:8025

# Prometheus (Metrics)
kubectl port-forward -n microservices svc/prometheus 9090:9090
# Visit: http://localhost:9090

# Grafana (Dashboards)
kubectl port-forward -n microservices svc/grafana 3000:3000
# Visit: http://localhost:3000
# Login: admin / admin
```

### Cleanup
```bash
./undeploy.sh  # or .\undeploy.ps1 on Windows
```

---

## Troubleshooting

### Pods not starting?
```bash
kubectl describe pod <pod-name> -n microservices
kubectl logs <pod-name> -n microservices
```

### Can't access services?
```bash
# Check if all pods are running
kubectl get pods -n microservices

# Check ingress
kubectl get ingress -n microservices
kubectl describe ingress microservices-ingress -n microservices
```

### Need to rebuild?
```bash
# Rebuild images
./build-images.sh  # or .\build-images.ps1

# For Minikube, load images
minikube image load api-gateway:latest
# ... repeat for all services

# Restart deployments
kubectl rollout restart deployment/api-gateway -n microservices
```

---

## Service Endpoints

Once deployed, access:

- **Main Documentation**: `http://<your-url>/`
- **User Service API**: `http://<your-url>/api/user-service/*`
- **Product Service API**: `http://<your-url>/api/product-service/*`
- **Order Service API**: `http://<your-url>/api/order-service/*`
- **Payment Service API**: `http://<your-url>/api/payment-service/*`
- **Notification Service API**: `http://<your-url>/api/notification-service/*`

## Monitoring

### Access Monitoring Tools

**Prometheus** (Metrics Collection):
```bash
kubectl port-forward -n microservices svc/prometheus 9090:9090
# Visit: http://localhost:9090
```

**Grafana** (Dashboards):
```bash
kubectl port-forward -n microservices svc/grafana 3000:3000
# Visit: http://localhost:3000
# Default credentials: admin / admin
```

### Service Metrics Endpoints

Each service exposes metrics at `/metrics`:
- API Gateway: `http://api-gateway:8000/metrics`
- User Service: `http://user-service:8000/metrics`
- Product Service: `http://product-service:8000/metrics`
- Order Service: `http://order-service:8000/metrics`
- Payment Service: `http://payment-service:8000/metrics`
- Notification Service: `http://notification-service:8000/metrics`

### Quick Prometheus Queries

- **Request Rate**: `rate(http_requests_total[5m])`
- **Error Rate**: `sum(rate(http_requests_total{status_code=~"5.."}[5m])) by (service)`
- **Response Time**: `rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])`

For more monitoring details, see [PROMETHEUS_MONITORING.md](../../PROMETHEUS_MONITORING.md).

---

For detailed instructions, see [README.md](README.md) and [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md).


