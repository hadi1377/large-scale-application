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

### 4. Access
```bash
# Port forward to access locally
kubectl port-forward -n microservices svc/api-gateway 8050:8000

# Visit: http://localhost:8050
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

---

For detailed instructions, see [README.md](README.md) and [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md).


