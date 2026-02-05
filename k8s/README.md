# Kubernetes Deployment Guide for Microservices

This directory contains Kubernetes manifests and deployment scripts for deploying the microservices architecture to a Kubernetes cluster.

## Architecture Overview

The application consists of the following components:

### Microservices
- **API Gateway**: Central entry point for all services (Port 8000)
- **User Service**: User management and authentication (Port 8000)
- **Product Service**: Product catalog management (Port 8000)
- **Order Service**: Order processing and management (Port 8000)
- **Payment Service**: Payment processing (Port 8000)
- **Notification Service**: Email notifications via RabbitMQ (Port 8000)

### Databases
- **PostgreSQL**: For User, Order, and Payment services
- **MongoDB**: For Product service

### Infrastructure
- **RabbitMQ**: Message broker for async communication
- **Mailpit**: Email testing tool

### Monitoring
- **Prometheus**: Metrics collection and storage
- **Grafana**: Metrics visualization and dashboards

## Directory Structure

```
k8s/
├── base/                     # Base configurations
│   ├── namespace.yaml        # Kubernetes namespace
│   ├── configmap.yaml        # Application configuration
│   └── secrets.yaml          # Sensitive data (passwords, API keys)
├── databases/                # Database StatefulSets
│   ├── user-db-statefulset.yaml
│   ├── order-db-statefulset.yaml
│   ├── payment-db-statefulset.yaml
│   └── product-db-statefulset.yaml
├── infrastructure/           # Infrastructure services
│   ├── rabbitmq-deployment.yaml
│   └── mailpit-deployment.yaml
├── monitoring/               # Monitoring stack
│   ├── prometheus-config.yaml
│   ├── prometheus-deployment.yaml
│   └── grafana-deployment.yaml
├── services/                 # Microservice deployments
│   ├── api-gateway-deployment.yaml
│   ├── user-service-deployment.yaml
│   ├── product-service-deployment.yaml
│   ├── order-service-deployment.yaml
│   ├── payment-service-deployment.yaml
│   └── notification-service-deployment.yaml
├── ingress/                  # Ingress configurations
│   ├── ingress.yaml
│   └── ingress-loadbalancer.yaml
├── build-images.sh          # Build Docker images (Linux/Mac)
├── build-images.ps1         # Build Docker images (Windows)
├── deploy.sh                # Deploy to Kubernetes (Linux/Mac)
├── deploy.ps1               # Deploy to Kubernetes (Windows)
├── undeploy.sh              # Remove from Kubernetes (Linux/Mac)
├── undeploy.ps1             # Remove from Kubernetes (Windows)
├── kustomization.yaml       # Kustomize configuration
└── README.md                # This file
```

## Prerequisites

### Required Tools
1. **Docker**: For building container images
2. **kubectl**: Kubernetes command-line tool
3. **Kubernetes Cluster**: One of the following:
   - **Minikube**: For local development
   - **Docker Desktop**: Built-in Kubernetes
   - **Cloud Provider**: GKE, AKS, or EKS

### Optional Tools
- **Helm**: For package management
- **k9s**: Terminal UI for Kubernetes
- **Lens**: Desktop Kubernetes IDE

## Setup Instructions

### Option 1: Deploy to Minikube (Local Development)

#### Step 1: Start Minikube
```bash
# Start Minikube with sufficient resources
minikube start --cpus=4 --memory=8192 --driver=docker

# Enable Ingress addon
minikube addons enable ingress
```

#### Step 2: Build and Load Docker Images
```bash
# Navigate to k8s directory
cd k8s

# Build images (Linux/Mac)
chmod +x build-images.sh deploy.sh undeploy.sh
./build-images.sh

# Or on Windows PowerShell
.\build-images.ps1
```

**Note**: The script will automatically navigate to the project root to find your service directories and build the images. It will then offer to load the images into Minikube.

#### Step 3: Deploy to Kubernetes
```bash
# Make sure you're in the k8s directory
# cd k8s  (if not already there)

# Deploy all services (Linux/Mac)
./deploy.sh

# Or on Windows PowerShell
.\deploy.ps1

# The script will automatically use the correct paths relative to the k8s directory
```

#### Step 4: Access the Services
```bash
# Get Minikube IP
minikube ip

# Add to /etc/hosts (Linux/Mac) or C:\Windows\System32\drivers\etc\hosts (Windows)
# <minikube-ip> microservices.local

# Or use port-forward
kubectl port-forward -n microservices svc/api-gateway 8000:8000

# Access at: http://localhost:8000
```

### Option 2: Deploy to Cloud (GKE, AKS, EKS)

#### Step 1: Configure kubectl
```bash
# For GKE
gcloud container clusters get-credentials <cluster-name> --region <region>

# For AKS
az aks get-credentials --resource-group <rg> --name <cluster-name>

# For EKS
aws eks update-kubeconfig --region <region> --name <cluster-name>
```

#### Step 2: Build and Push Docker Images
```bash
# Tag images for your container registry
docker tag api-gateway:latest <registry>/api-gateway:latest
docker tag user-service:latest <registry>/user-service:latest
docker tag product-service:latest <registry>/product-service:latest
docker tag order-service:latest <registry>/order-service:latest
docker tag payment-service:latest <registry>/payment-service:latest
docker tag notification-service:latest <registry>/notification-service:latest

# Push to registry
docker push <registry>/api-gateway:latest
docker push <registry>/user-service:latest
docker push <registry>/product-service:latest
docker push <registry>/order-service:latest
docker push <registry>/payment-service:latest
docker push <registry>/notification-service:latest
```

**Note**: Update the `image:` fields in all deployment YAML files to use your registry URL.

#### Step 3: Install NGINX Ingress Controller
```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Wait for the controller to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

#### Step 4: Deploy Services
```bash
# Deploy all services
./deploy.sh  # Linux/Mac
# or
.\deploy.ps1  # Windows
```

#### Step 5: Get Ingress URL
```bash
# Get external IP
kubectl get ingress -n microservices

# Update DNS or use the IP directly
```

### Option 3: Deploy with Kustomize
```bash
# Deploy using kustomize
kubectl apply -k .

# Or using kubectl with kustomization
kubectl kustomize . | kubectl apply -f -
```

## Configuration

### Environment Variables
All configuration is managed through ConfigMaps and Secrets. Edit these files before deployment:

- **base/configmap.yaml**: Application configuration
- **base/secrets.yaml**: Database passwords and API keys

### Scaling Services
```bash
# Scale a specific service
kubectl scale deployment/user-service -n microservices --replicas=3

# Or edit the deployment YAML file and reapply
kubectl apply -f services/user-service-deployment.yaml
```

### Resource Limits
Resource requests and limits are defined in each deployment file. Adjust based on your needs:

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "500m"
```

## Monitoring and Debugging

### View All Resources
```bash
kubectl get all -n microservices
```

### Check Pod Status
```bash
kubectl get pods -n microservices
kubectl describe pod <pod-name> -n microservices
```

### View Logs
```bash
# View logs for a specific service
kubectl logs -f deployment/api-gateway -n microservices

# View logs for all pods of a service
kubectl logs -f -l app=user-service -n microservices

# View previous container logs
kubectl logs <pod-name> -n microservices --previous
```

### Exec into a Pod
```bash
kubectl exec -it <pod-name> -n microservices -- /bin/sh
```

### Port Forwarding
```bash
# Forward API Gateway
kubectl port-forward -n microservices svc/api-gateway 8000:8000

# Forward RabbitMQ Management UI
kubectl port-forward -n microservices svc/rabbitmq 15672:15672

# Forward Mailpit UI
kubectl port-forward -n microservices svc/mailpit 8025:8025

# Forward Prometheus
kubectl port-forward -n microservices svc/prometheus 9090:9090

# Forward Grafana
kubectl port-forward -n microservices svc/grafana 3000:3000

# Forward PostgreSQL (User DB)
kubectl port-forward -n microservices svc/user-db 5432:5432
```

### Check Ingress
```bash
# Get Ingress details
kubectl get ingress -n microservices
kubectl describe ingress microservices-ingress -n microservices

# Check Ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller
```

## Service Endpoints

### API Gateway
- **Base URL**: `http://<ingress-url>` or `http://localhost:8000`
- **Documentation**: `http://<ingress-url>/`
- **Health Check**: `http://<ingress-url>/health`

### Service-Specific Docs
- **User Service**: `http://<ingress-url>/docs/user-service`
- **Product Service**: `http://<ingress-url>/docs/product-service`
- **Order Service**: `http://<ingress-url>/docs/order-service`
- **Payment Service**: `http://<ingress-url>/docs/payment-service`
- **Notification Service**: `http://<ingress-url>/docs/notification-service`

### API Proxy
- **User API**: `http://<ingress-url>/api/user-service/*`
- **Product API**: `http://<ingress-url>/api/product-service/*`
- **Order API**: `http://<ingress-url>/api/order-service/*`
- **Payment API**: `http://<ingress-url>/api/payment-service/*`
- **Notification API**: `http://<ingress-url>/api/notification-service/*`

### Management UIs
- **RabbitMQ Management**: `http://<ingress-url>/rabbitmq`
  - Default credentials: `rabbitmq_user` / `rabbitmq_password`
- **Mailpit Web UI**: `http://<ingress-url>/mailpit`
  - No authentication required

### Monitoring UIs
- **Prometheus**: `http://localhost:9090` (via port-forward)
  - Query metrics, view targets, create alerts
- **Grafana**: `http://localhost:3000` (via port-forward)
  - Default credentials: `admin` / `admin` (⚠️ Change in production!)
  - Pre-configured with Prometheus datasource
  - Create dashboards to visualize service metrics

**Note**: For Minikube, use port-forwarding for easier access:
```bash
# RabbitMQ
kubectl port-forward -n microservices svc/rabbitmq 15672:15672
# Access: http://localhost:15672

# Mailpit
kubectl port-forward -n microservices svc/mailpit 8025:8025
# Access: http://localhost:8025
```

## Persistent Data

### Volumes
Each database uses a PersistentVolumeClaim (PVC) for data persistence:
- User DB: 1Gi
- Order DB: 1Gi
- Payment DB: 1Gi
- Product DB: 2Gi
- RabbitMQ: 1Gi

### View PVCs
```bash
kubectl get pvc -n microservices
```

### Backup Database
```bash
# Example: Backup User DB
kubectl exec -n microservices user-db-0 -- pg_dump -U user_db_user user_db > user_db_backup.sql
```

### Restore Database
```bash
# Example: Restore User DB
kubectl exec -i -n microservices user-db-0 -- psql -U user_db_user user_db < user_db_backup.sql
```

## Cleanup

### Remove All Resources
```bash
# Remove all deployed resources (Linux/Mac)
./undeploy.sh

# Or on Windows PowerShell
.\undeploy.ps1
```

### Delete Specific Resources
```bash
# Delete a specific deployment
kubectl delete deployment user-service -n microservices

# Delete the entire namespace (WARNING: Deletes everything including data!)
kubectl delete namespace microservices
```

## Troubleshooting

### Pods Not Starting
1. Check pod status: `kubectl describe pod <pod-name> -n microservices`
2. Check logs: `kubectl logs <pod-name> -n microservices`
3. Verify images are available: `docker images | grep <service-name>`
4. Check resource limits: `kubectl top pods -n microservices`

### Database Connection Issues
1. Check if database pods are running: `kubectl get pods -n microservices | grep db`
2. Verify ConfigMap: `kubectl get configmap app-config -n microservices -o yaml`
3. Test connection from service pod:
   ```bash
   kubectl exec -it <service-pod> -n microservices -- /bin/sh
   nc -zv user-db 5432
   ```

### Service Communication Issues
1. Check service endpoints: `kubectl get endpoints -n microservices`
2. Test service DNS: 
   ```bash
   kubectl run test --image=busybox -n microservices --rm -it -- nslookup user-service
   ```
3. Check network policies: `kubectl get networkpolicies -n microservices`

### Ingress Not Working
1. Check Ingress status: `kubectl describe ingress microservices-ingress -n microservices`
2. Verify Ingress controller is running: `kubectl get pods -n ingress-nginx`
3. Check Ingress controller logs: `kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller`
4. Test without Ingress using port-forward

### Image Pull Errors
For Minikube:
```bash
# Rebuild and load images
./build-images.sh
minikube image load <image-name>:latest

# Or use Minikube's Docker daemon
eval $(minikube docker-env)
./build-images.sh
```

For cloud:
```bash
# Ensure images are pushed to container registry
docker push <registry>/<image-name>:latest

# Update imagePullSecrets if using private registry
```

## Production Considerations

### Security
1. **Change default passwords** in `base/secrets.yaml`
2. **Use Kubernetes Secrets** properly (consider using sealed-secrets or external secret managers)
3. **Enable RBAC** and create service accounts
4. **Use Network Policies** to restrict pod-to-pod communication
5. **Enable TLS** for Ingress (add certificates)
6. **Scan images** for vulnerabilities

### High Availability
1. **Increase replicas** for critical services
2. **Use multiple zones** for cloud deployments
3. **Set up database replication** (StatefulSet with replicas > 1)
4. **Configure Pod Disruption Budgets**
5. **Use HorizontalPodAutoscaler** for auto-scaling

### Monitoring

#### Prometheus and Grafana

The monitoring stack is already configured and ready to deploy:

```bash
# Deploy Prometheus configuration
kubectl apply -f monitoring/prometheus-config.yaml

# Deploy Prometheus
kubectl apply -f monitoring/prometheus-deployment.yaml

# Deploy Grafana
kubectl apply -f monitoring/grafana-deployment.yaml

# Wait for services to be ready
kubectl wait --for=condition=ready pod -l app=prometheus -n microservices --timeout=120s
kubectl wait --for=condition=ready pod -l app=grafana -n microservices --timeout=120s
```

**Access Prometheus**:
```bash
kubectl port-forward -n microservices svc/prometheus 9090:9090
# Visit: http://localhost:9090
```

**Access Grafana**:
```bash
kubectl port-forward -n microservices svc/grafana 3000:3000
# Visit: http://localhost:3000
# Default credentials: admin / admin (⚠️ Change in production!)
```

**Service Metrics**: All services automatically expose Prometheus metrics at `/metrics`:
- `http://api-gateway:8000/metrics`
- `http://user-service:8000/metrics`
- `http://product-service:8000/metrics`
- `http://order-service:8000/metrics`
- `http://payment-service:8000/metrics`
- `http://notification-service:8000/metrics`

**Example Prometheus Queries**:
- Request rate: `rate(http_requests_total[5m])`
- Error rate: `sum(rate(http_requests_total{status_code=~"5.."}[5m])) by (service)`
- Average response time: `rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])`
- 95th percentile: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`

For detailed monitoring setup and usage, see [PROMETHEUS_MONITORING.md](../../PROMETHEUS_MONITORING.md).

#### Additional Monitoring (Optional)
1. **Set up ELK/EFK stack** for centralized logging
2. **Configure alerts** in Prometheus for critical issues
3. **Use Jaeger or Zipkin** for distributed tracing
4. **Set up alerting** with Alertmanager

### Backup Strategy
1. **Schedule regular database backups**
2. **Back up PersistentVolumes**
3. **Version control** all Kubernetes manifests
4. **Document disaster recovery procedures**

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Kustomize Documentation](https://kustomize.io/)

## Support

For issues or questions:
1. Check the logs: `kubectl logs -f <pod-name> -n microservices`
2. Review the troubleshooting section above
3. Check Kubernetes events: `kubectl get events -n microservices --sort-by='.lastTimestamp'`
4. Consult the service-specific documentation

---

**Note**: This is a development/staging deployment. For production use, please review the "Production Considerations" section and adjust configurations accordingly.


