#!/bin/bash

# Deploy all microservices to Kubernetes
set -e

echo "Deploying microservices to Kubernetes..."

# Get the script directory and navigate to it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create namespace
echo "Creating namespace..."
kubectl apply -f base/namespace.yaml

# Create ConfigMaps and Secrets
echo "Creating ConfigMaps and Secrets..."
kubectl apply -f base/configmap.yaml
kubectl apply -f base/secrets.yaml

# Deploy databases
echo "Deploying databases..."
kubectl apply -f databases/user-db-statefulset.yaml
kubectl apply -f databases/order-db-statefulset.yaml
kubectl apply -f databases/payment-db-statefulset.yaml
kubectl apply -f databases/product-db-statefulset.yaml

# Deploy infrastructure services
echo "Deploying infrastructure services..."
kubectl apply -f infrastructure/rabbitmq-deployment.yaml
kubectl apply -f infrastructure/mailpit-deployment.yaml

# Wait for databases and infrastructure to be ready
echo "Waiting for databases and infrastructure to be ready..."
kubectl wait --for=condition=ready pod -l app=user-db -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=order-db -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=payment-db -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=product-db -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=rabbitmq -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=mailpit -n microservices --timeout=300s

# Deploy microservices
echo "Deploying microservices..."
kubectl apply -f services/user-service-deployment.yaml
kubectl apply -f services/product-service-deployment.yaml
kubectl apply -f services/order-service-deployment.yaml
kubectl apply -f services/payment-service-deployment.yaml
kubectl apply -f services/notification-service-deployment.yaml
kubectl apply -f services/api-gateway-deployment.yaml

# Wait for services to be ready
echo "Waiting for microservices to be ready..."
sleep 10
kubectl wait --for=condition=ready pod -l app=user-service -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=product-service -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=order-service -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=payment-service -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=notification-service -n microservices --timeout=300s
kubectl wait --for=condition=ready pod -l app=api-gateway -n microservices --timeout=300s

# Deploy Ingress
echo "Deploying Ingress..."
kubectl apply -f ingress/ingress.yaml

echo ""
echo "Deployment complete!"
echo ""
echo "To check the status of your deployment:"
echo "  kubectl get all -n microservices"
echo ""
echo "To get the Ingress URL:"
echo "  kubectl get ingress -n microservices"
echo ""
echo "To access the API Gateway:"
echo "  For Minikube: minikube service api-gateway -n microservices"
echo "  For cloud: Use the LoadBalancer IP or Ingress URL"
echo ""
echo "To forward the API Gateway port locally:"
echo "  kubectl port-forward -n microservices svc/api-gateway 8000:8000"
echo "  Then visit: http://localhost:8000"


