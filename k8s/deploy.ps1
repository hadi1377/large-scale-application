# PowerShell script to deploy all microservices to Kubernetes

Write-Host "Deploying microservices to Kubernetes..." -ForegroundColor Green

# Get the script directory and navigate to it
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "Working directory: $ScriptDir" -ForegroundColor Cyan

# Create namespace
Write-Host "Creating namespace..." -ForegroundColor Yellow
kubectl apply -f base/namespace.yaml

# Create ConfigMaps and Secrets
Write-Host "Creating ConfigMaps and Secrets..." -ForegroundColor Yellow
kubectl apply -f base/configmap.yaml
kubectl apply -f base/secrets.yaml

# Deploy databases
Write-Host "Deploying databases..." -ForegroundColor Yellow
kubectl apply -f databases/user-db-statefulset.yaml
kubectl apply -f databases/order-db-statefulset.yaml
kubectl apply -f databases/payment-db-statefulset.yaml
kubectl apply -f databases/product-db-statefulset.yaml

# Deploy infrastructure services
Write-Host "Deploying infrastructure services..." -ForegroundColor Yellow
kubectl apply -f infrastructure/rabbitmq-deployment.yaml
kubectl apply -f infrastructure/mailpit-deployment.yaml

# Wait for databases and infrastructure to be ready
Write-Host "Waiting for databases and infrastructure to be ready..." -ForegroundColor Yellow
kubectl wait --for=condition=ready pod -l app=user-db -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=order-db -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=payment-db -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=product-db -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=rabbitmq -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=mailpit -n microservices --timeout=300s

# Deploy microservices
Write-Host "Deploying microservices..." -ForegroundColor Yellow
kubectl apply -f services/user-service-deployment.yaml
kubectl apply -f services/product-service-deployment.yaml
kubectl apply -f services/order-service-deployment.yaml
kubectl apply -f services/payment-service-deployment.yaml
kubectl apply -f services/notification-service-deployment.yaml
kubectl apply -f services/api-gateway-deployment.yaml

# Wait for services to be ready
Write-Host "Waiting for microservices to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
kubectl wait --for=condition=ready pod -l app=user-service -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=product-service -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=order-service -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=payment-service -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=notification-service -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=api-gateway -n microservices --timeout=300s

# Deploy Ingress
Write-Host "Deploying Ingress..." -ForegroundColor Yellow
kubectl apply -f ingress/ingress.yaml

# Deploy monitoring (optional)
if (Test-Path "monitoring") {
    Write-Host ""
    Write-Host "Deploying monitoring stack..." -ForegroundColor Yellow
    kubectl apply -f monitoring/prometheus-config.yaml
    kubectl apply -f monitoring/prometheus-deployment.yaml
    kubectl apply -f monitoring/grafana-deployment.yaml
    Write-Host "Monitoring stack deployed!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To check the status of your deployment:" -ForegroundColor Cyan
Write-Host "  kubectl get all -n microservices"
Write-Host ""
Write-Host "To get the Ingress URL:" -ForegroundColor Cyan
Write-Host "  kubectl get ingress -n microservices"
Write-Host ""
Write-Host "To access the API Gateway:" -ForegroundColor Cyan
Write-Host "  For Minikube: minikube service api-gateway -n microservices"
Write-Host "  For cloud: Use the LoadBalancer IP or Ingress URL"
Write-Host ""
Write-Host "To forward the API Gateway port locally:" -ForegroundColor Cyan
Write-Host "  kubectl port-forward -n microservices svc/api-gateway 8000:8000"
Write-Host "  Then visit: http://localhost:8000"
if (Test-Path "monitoring") {
    Write-Host ""
    Write-Host "To access monitoring:" -ForegroundColor Cyan
    Write-Host "  Prometheus: kubectl port-forward -n microservices svc/prometheus 9090:9090"
    Write-Host "  Grafana: kubectl port-forward -n microservices svc/grafana 3000:3000"
    Write-Host "  Grafana login: admin / admin"
}


