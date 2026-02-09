# Cloud Deployment Guide

This guide provides specific instructions for deploying the microservices to major cloud providers.

## Table of Contents
- [Google Kubernetes Engine (GKE)](#google-kubernetes-engine-gke)
- [Amazon Elastic Kubernetes Service (EKS)](#amazon-elastic-kubernetes-service-eks)
- [Azure Kubernetes Service (AKS)](#azure-kubernetes-service-aks)
- [Digital Ocean Kubernetes](#digitalocean-kubernetes)

---

## Google Kubernetes Engine (GKE)

### Prerequisites
- Google Cloud SDK installed
- gcloud CLI configured
- Project created on Google Cloud

### Step 1: Create GKE Cluster
```bash
# Set project
gcloud config set project <your-project-id>

# Create cluster
gcloud container clusters create microservices-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --disk-size 50 \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 5

# Get credentials
gcloud container clusters get-credentials microservices-cluster --zone us-central1-a
```

### Step 2: Set Up Container Registry
```bash
# Enable Container Registry
gcloud services enable containerregistry.googleapis.com

# Configure Docker
gcloud auth configure-docker

# Build and tag images
docker build -t gcr.io/<project-id>/api-gateway:latest ./api-gateway
docker build -t gcr.io/<project-id>/user-service:latest ./user-service
docker build -t gcr.io/<project-id>/product-service:latest ./product-service
docker build -t gcr.io/<project-id>/order-service:latest ./order-service
docker build -t gcr.io/<project-id>/payment-service:latest ./payment-service
docker build -t gcr.io/<project-id>/notification-service:latest ./notification-service

# Push images
docker push gcr.io/<project-id>/api-gateway:latest
docker push gcr.io/<project-id>/user-service:latest
docker push gcr.io/<project-id>/product-service:latest
docker push gcr.io/<project-id>/order-service:latest
docker push gcr.io/<project-id>/payment-service:latest
docker push gcr.io/<project-id>/notification-service:latest
```

### Step 3: Update Deployment Files
Update the `image:` field in all service deployment files:
```yaml
image: gcr.io/<project-id>/user-service:latest
```

### Step 4: Install NGINX Ingress Controller
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
```

### Step 5: Deploy Services
```bash
cd k8s
./deploy.sh
```

### Step 6: Configure DNS
```bash
# Get external IP
kubectl get ingress -n microservices

# Add A record in your DNS provider pointing to the external IP
# Or use Google Cloud DNS
gcloud dns record-sets create microservices.yourdomain.com \
  --zone=your-zone \
  --type=A \
  --ttl=300 \
  --rrdatas=<external-ip>
```

### Step 7: Enable HTTPS (Optional)
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Update ingress with TLS
# Add to ingress/ingress.yaml:
#   tls:
#   - hosts:
#     - microservices.yourdomain.com
#     secretName: microservices-tls
#   annotations:
#     cert-manager.io/cluster-issuer: "letsencrypt-prod"
```

### Cost Optimization
```bash
# Use preemptible nodes for dev/test
gcloud container node-pools create preemptible-pool \
  --cluster=microservices-cluster \
  --zone=us-central1-a \
  --preemptible \
  --num-nodes=2 \
  --machine-type=n1-standard-2
```

---

## Amazon Elastic Kubernetes Service (EKS)

### Prerequisites
- AWS CLI installed and configured
- eksctl installed
- kubectl installed

### Step 1: Create EKS Cluster
```bash
# Create cluster using eksctl
eksctl create cluster \
  --name microservices-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5 \
  --managed

# Update kubeconfig
aws eks update-kubeconfig --region us-east-1 --name microservices-cluster
```

### Step 2: Set Up Amazon ECR
```bash
# Create ECR repositories
aws ecr create-repository --repository-name api-gateway --region us-east-1
aws ecr create-repository --repository-name user-service --region us-east-1
aws ecr create-repository --repository-name product-service --region us-east-1
aws ecr create-repository --repository-name order-service --region us-east-1
aws ecr create-repository --repository-name payment-service --region us-east-1
aws ecr create-repository --repository-name notification-service --region us-east-1

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and tag images
docker build -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/api-gateway:latest ./api-gateway
docker build -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/user-service:latest ./user-service
docker build -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/product-service:latest ./product-service
docker build -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/order-service:latest ./order-service
docker build -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/payment-service:latest ./payment-service
docker build -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/notification-service:latest ./notification-service

# Push images
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/api-gateway:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/user-service:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/product-service:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/order-service:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/payment-service:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/notification-service:latest
```

### Step 3: Update Deployment Files
Update the `image:` field in all service deployment files:
```yaml
image: <account-id>.dkr.ecr.us-east-1.amazonaws.com/user-service:latest
```

### Step 4: Install AWS Load Balancer Controller
```bash
# Create IAM policy
curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.6.0/docs/install/iam_policy.json

aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam_policy.json

# Create IAM role
eksctl create iamserviceaccount \
  --cluster=microservices-cluster \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --attach-policy-arn=arn:aws:iam::<account-id>:policy/AWSLoadBalancerControllerIAMPolicy \
  --override-existing-serviceaccounts \
  --approve

# Install controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"

helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=microservices-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

### Step 5: Deploy Services
```bash
cd k8s
./deploy.sh
```

### Step 6: Use ALB Ingress (Alternative to NGINX)
Update `ingress/ingress.yaml`:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: microservices-ingress
  namespace: microservices
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
  - host: microservices.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 8000
```

### Cost Optimization
```bash
# Use Fargate for serverless
eksctl create fargateprofile \
  --cluster microservices-cluster \
  --name microservices-profile \
  --namespace microservices

# Use Spot instances
eksctl create nodegroup \
  --cluster=microservices-cluster \
  --spot \
  --name=spot-workers \
  --node-type=t3.medium \
  --nodes=2
```

---

## Azure Kubernetes Service (AKS)

### Prerequisites
- Azure CLI installed
- Azure subscription active

### Step 1: Create AKS Cluster
```bash
# Login to Azure
az login

# Create resource group
az group create --name microservices-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group microservices-rg \
  --name microservices-cluster \
  --node-count 3 \
  --node-vm-size Standard_D2s_v3 \
  --enable-managed-identity \
  --generate-ssh-keys \
  --enable-cluster-autoscaler \
  --min-count 2 \
  --max-count 5

# Get credentials
az aks get-credentials --resource-group microservices-rg --name microservices-cluster
```

### Step 2: Set Up Azure Container Registry (ACR)
```bash
# Create ACR
az acr create --resource-group microservices-rg --name microservicesacr --sku Basic

# Login to ACR
az acr login --name microservicesacr

# Attach ACR to AKS
az aks update -n microservices-cluster -g microservices-rg --attach-acr microservicesacr

# Build and push images
az acr build --registry microservicesacr --image api-gateway:latest ./api-gateway
az acr build --registry microservicesacr --image user-service:latest ./user-service
az acr build --registry microservicesacr --image product-service:latest ./product-service
az acr build --registry microservicesacr --image order-service:latest ./order-service
az acr build --registry microservicesacr --image payment-service:latest ./payment-service
az acr build --registry microservicesacr --image notification-service:latest ./notification-service
```

### Step 3: Update Deployment Files
Update the `image:` field in all service deployment files:
```yaml
image: microservicesacr.azurecr.io/user-service:latest
```

### Step 4: Install NGINX Ingress Controller
```bash
# Install using Helm
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.annotations."service\.beta\.kubernetes\.io/azure-load-balancer-health-probe-request-path"=/healthz
```

### Step 5: Deploy Services
```bash
cd k8s
./deploy.sh
```

### Step 6: Configure DNS
```bash
# Get external IP
kubectl get service -n ingress-nginx

# Create DNS zone and record
az network dns zone create -g microservices-rg -n yourdomain.com

az network dns record-set a add-record \
  -g microservices-rg \
  -z yourdomain.com \
  -n microservices \
  -a <external-ip>
```

### Cost Optimization
```bash
# Use Azure Spot VMs
az aks nodepool add \
  --resource-group microservices-rg \
  --cluster-name microservices-cluster \
  --name spotpool \
  --priority Spot \
  --eviction-policy Delete \
  --spot-max-price -1 \
  --node-count 2 \
  --node-vm-size Standard_D2s_v3
```

---

## DigitalOcean Kubernetes

### Prerequisites
- doctl CLI installed
- DigitalOcean account

### Step 1: Create Kubernetes Cluster
```bash
# Authenticate
doctl auth init

# Create cluster
doctl kubernetes cluster create microservices-cluster \
  --region nyc1 \
  --size s-2vcpu-4gb \
  --count 3 \
  --auto-upgrade=true

# Get credentials
doctl kubernetes cluster kubeconfig save microservices-cluster
```

### Step 2: Set Up Container Registry
```bash
# Create registry
doctl registry create microservices-registry

# Login
doctl registry login

# Build and tag images
docker build -t registry.digitalocean.com/microservices-registry/api-gateway:latest ./api-gateway
docker build -t registry.digitalocean.com/microservices-registry/user-service:latest ./user-service
# ... (repeat for all services)

# Push images
docker push registry.digitalocean.com/microservices-registry/api-gateway:latest
docker push registry.digitalocean.com/microservices-registry/user-service:latest
# ... (repeat for all services)

# Integrate registry with cluster
doctl kubernetes cluster registry add microservices-cluster
```

### Step 3: Install NGINX Ingress Controller
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/do/deploy.yaml
```

### Step 4: Deploy Services
```bash
cd k8s
./deploy.sh
```

---

## General Best Practices for Cloud Deployments

### 1. Use Managed Databases (Production)
Consider using managed database services instead of running databases in Kubernetes:
- **GKE**: Cloud SQL
- **EKS**: Amazon RDS
- **AKS**: Azure Database

### 2. Set Up Monitoring
```bash
# Install Prometheus and Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
```

### 3. Configure Auto-Scaling
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
  namespace: microservices
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 4. Use Secrets Management
- **GKE**: Google Secret Manager
- **EKS**: AWS Secrets Manager
- **AKS**: Azure Key Vault

### 5. Enable Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-gateway
  namespace: microservices
spec:
  podSelector:
    matchLabels:
      app: user-service
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - protocol: TCP
      port: 8000
```

### 6. Set Up CI/CD
Example using GitHub Actions:
```yaml
name: Deploy to Kubernetes
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build and push images
        run: |
          docker build -t <registry>/api-gateway:${{ github.sha }} ./api-gateway
          docker push <registry>/api-gateway:${{ github.sha }}
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/api-gateway api-gateway=<registry>/api-gateway:${{ github.sha }} -n microservices
```

---

## Troubleshooting Cloud-Specific Issues

### Load Balancer Not Getting External IP
```bash
# Check service
kubectl get svc -n ingress-nginx

# Check cloud provider load balancer
# GKE
gcloud compute forwarding-rules list

# EKS
aws elb describe-load-balancers

# AKS
az network lb list
```

### Image Pull Errors in Cloud
```bash
# Verify registry access
# GKE - ensure service account has access
# EKS - check ECR permissions
# AKS - verify ACR integration

# Create image pull secret if needed
kubectl create secret docker-registry regcred \
  --docker-server=<registry-url> \
  --docker-username=<username> \
  --docker-password=<password> \
  -n microservices
```

---

For more detailed cloud-specific configurations, refer to the official documentation of each cloud provider.





