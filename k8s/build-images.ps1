# PowerShell script to build all Docker images for the microservices

Write-Host "Building Docker images for microservices..." -ForegroundColor Green

# Get the script directory and navigate to project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "Project root: $ProjectRoot" -ForegroundColor Cyan
Set-Location $ProjectRoot

# Build API Gateway
Write-Host "Building api-gateway..." -ForegroundColor Yellow
docker build -t api-gateway:latest ./api-gateway

# Build User Service
Write-Host "Building user-service..." -ForegroundColor Yellow
docker build -t user-service:latest ./user-service

# Build Product Service
Write-Host "Building product-service..." -ForegroundColor Yellow
docker build -t product-service:latest ./product-service

# Build Order Service
Write-Host "Building order-service..." -ForegroundColor Yellow
docker build -t order-service:latest ./order-service

# Build Payment Service
Write-Host "Building payment-service..." -ForegroundColor Yellow
docker build -t payment-service:latest ./payment-service

# Build Notification Service
Write-Host "Building notification-service..." -ForegroundColor Yellow
docker build -t notification-service:latest ./notification-service

Write-Host "All images built successfully!" -ForegroundColor Green

# Optional: If using Minikube, load images into Minikube
if (Get-Command minikube -ErrorAction SilentlyContinue) {
    $response = Read-Host "Do you want to load images into Minikube? (y/n)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "Loading images into Minikube..." -ForegroundColor Yellow
        minikube image load api-gateway:latest
        minikube image load user-service:latest
        minikube image load product-service:latest
        minikube image load order-service:latest
        minikube image load payment-service:latest
        minikube image load notification-service:latest
        Write-Host "Images loaded into Minikube!" -ForegroundColor Green
    }
}

Write-Host "Done!" -ForegroundColor Green


