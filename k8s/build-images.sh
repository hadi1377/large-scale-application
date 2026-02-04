#!/bin/bash

# Build all Docker images for the microservices
# This script builds images for local deployment

set -e

echo "Building Docker images for microservices..."

# Get the script directory and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Project root: $PROJECT_ROOT"
cd "$PROJECT_ROOT"

# Build API Gateway
echo "Building api-gateway..."
docker build -t api-gateway:latest ./api-gateway

# Build User Service
echo "Building user-service..."
docker build -t user-service:latest ./user-service

# Build Product Service
echo "Building product-service..."
docker build -t product-service:latest ./product-service

# Build Order Service
echo "Building order-service..."
docker build -t order-service:latest ./order-service

# Build Payment Service
echo "Building payment-service..."
docker build -t payment-service:latest ./payment-service

# Build Notification Service
echo "Building notification-service..."
docker build -t notification-service:latest ./notification-service

echo "All images built successfully!"

# Optional: If using Minikube, load images into Minikube
if command -v minikube &> /dev/null; then
    read -p "Do you want to load images into Minikube? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Loading images into Minikube..."
        minikube image load api-gateway:latest
        minikube image load user-service:latest
        minikube image load product-service:latest
        minikube image load order-service:latest
        minikube image load payment-service:latest
        minikube image load notification-service:latest
        echo "Images loaded into Minikube!"
    fi
fi

echo "Done!"


