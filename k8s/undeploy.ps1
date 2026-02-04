# PowerShell script to remove all microservices from Kubernetes

Write-Host "Removing microservices from Kubernetes..." -ForegroundColor Yellow

# Get the script directory and navigate to it
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "Working directory: $ScriptDir" -ForegroundColor Cyan

# Delete Ingress
Write-Host "Deleting Ingress..." -ForegroundColor Yellow
kubectl delete -f ingress/ingress.yaml --ignore-not-found=true

# Delete microservices
Write-Host "Deleting microservices..." -ForegroundColor Yellow
kubectl delete -f services/api-gateway-deployment.yaml --ignore-not-found=true
kubectl delete -f services/notification-service-deployment.yaml --ignore-not-found=true
kubectl delete -f services/payment-service-deployment.yaml --ignore-not-found=true
kubectl delete -f services/order-service-deployment.yaml --ignore-not-found=true
kubectl delete -f services/product-service-deployment.yaml --ignore-not-found=true
kubectl delete -f services/user-service-deployment.yaml --ignore-not-found=true

# Delete infrastructure services
Write-Host "Deleting infrastructure services..." -ForegroundColor Yellow
kubectl delete -f infrastructure/mailpit-deployment.yaml --ignore-not-found=true
kubectl delete -f infrastructure/rabbitmq-deployment.yaml --ignore-not-found=true

# Delete databases
Write-Host "Deleting databases..." -ForegroundColor Yellow
kubectl delete -f databases/product-db-statefulset.yaml --ignore-not-found=true
kubectl delete -f databases/payment-db-statefulset.yaml --ignore-not-found=true
kubectl delete -f databases/order-db-statefulset.yaml --ignore-not-found=true
kubectl delete -f databases/user-db-statefulset.yaml --ignore-not-found=true

# Delete ConfigMaps and Secrets
Write-Host "Deleting ConfigMaps and Secrets..." -ForegroundColor Yellow
kubectl delete -f base/secrets.yaml --ignore-not-found=true
kubectl delete -f base/configmap.yaml --ignore-not-found=true

# Delete namespace (this will also delete all PVCs)
Write-Host "Deleting namespace..." -ForegroundColor Yellow
kubectl delete -f base/namespace.yaml --ignore-not-found=true

Write-Host "Cleanup complete!" -ForegroundColor Green


