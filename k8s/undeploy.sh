#!/bin/bash

# Remove all microservices from Kubernetes
set -e

echo "Removing microservices from Kubernetes..."

# Get the script directory and navigate to it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Delete Ingress
echo "Deleting Ingress..."
kubectl delete -f ingress/ingress.yaml --ignore-not-found=true

# Delete microservices
echo "Deleting microservices..."
kubectl delete -f services/api-gateway-deployment.yaml --ignore-not-found=true
kubectl delete -f services/notification-service-deployment.yaml --ignore-not-found=true
kubectl delete -f services/payment-service-deployment.yaml --ignore-not-found=true
kubectl delete -f services/order-service-deployment.yaml --ignore-not-found=true
kubectl delete -f services/product-service-deployment.yaml --ignore-not-found=true
kubectl delete -f services/user-service-deployment.yaml --ignore-not-found=true

# Delete infrastructure services
echo "Deleting infrastructure services..."
kubectl delete -f infrastructure/mailpit-deployment.yaml --ignore-not-found=true
kubectl delete -f infrastructure/rabbitmq-deployment.yaml --ignore-not-found=true

# Delete databases
echo "Deleting databases..."
kubectl delete -f databases/product-db-statefulset.yaml --ignore-not-found=true
kubectl delete -f databases/payment-db-statefulset.yaml --ignore-not-found=true
kubectl delete -f databases/order-db-statefulset.yaml --ignore-not-found=true
kubectl delete -f databases/user-db-statefulset.yaml --ignore-not-found=true

# Delete ConfigMaps and Secrets
echo "Deleting ConfigMaps and Secrets..."
kubectl delete -f base/secrets.yaml --ignore-not-found=true
kubectl delete -f base/configmap.yaml --ignore-not-found=true

# Delete namespace (this will also delete all PVCs)
echo "Deleting namespace..."
kubectl delete -f base/namespace.yaml --ignore-not-found=true

echo "Cleanup complete!"


