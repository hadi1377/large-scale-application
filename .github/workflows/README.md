# GitHub Actions CI/CD Setup Guide

This repository includes GitHub Actions workflows for continuous integration and continuous deployment.

## Workflows Overview

### 1. CI Workflow (`.github/workflows/ci.yml`)
- **Triggers**: Push and Pull Requests to `main`, `master`, or `develop` branches
- **Jobs**:
  - **Test**: Runs unit tests for each microservice in parallel
  - **Build**: Builds Docker images for all services (only on push, not PRs)
  - **Test All**: Runs the comprehensive test suite using `run_tests.py`

### 2. CD Workflow (`.github/workflows/cd.yml`)
- **Triggers**: 
  - Push to `main` or `master` branch
  - Tags matching `v*.*.*` pattern (e.g., `v1.0.0`)
  - Manual workflow dispatch
- **Jobs**:
  - **Deploy**: Deploys all services to Kubernetes

## Setup Instructions

### Step 1: Enable GitHub Actions

1. Go to your GitHub repository
2. Navigate to **Settings** → **Actions** → **General**
3. Ensure "Allow all actions and reusable workflows" is enabled
4. Save the changes

### Step 2: Configure Container Registry (Optional but Recommended)

The workflows use GitHub Container Registry (ghcr.io) by default. No additional setup is needed as it uses `GITHUB_TOKEN` automatically.

**Alternative: Docker Hub**

If you prefer Docker Hub, modify `.github/workflows/ci.yml`:

```yaml
- name: Log in to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```

Then add secrets:
- `DOCKERHUB_USERNAME`: Your Docker Hub username
- `DOCKERHUB_TOKEN`: Your Docker Hub access token

### Step 3: Configure Kubernetes Deployment (For CD Workflow)

#### Option A: Using kubeconfig file (Local/Minikube)

1. Get your kubeconfig:
   ```bash
   # For Minikube
   minikube kubectl config view --flatten > kubeconfig.yaml
   
   # Or copy your existing kubeconfig
   cat ~/.kube/config > kubeconfig.yaml
   ```

2. Encode it to base64:
   ```bash
   # On Linux/Mac
   base64 -i kubeconfig.yaml
   
   # On Windows PowerShell
   [Convert]::ToBase64String([IO.File]::ReadAllBytes("kubeconfig.yaml"))
   ```

3. Add GitHub Secret:
   - Go to **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `KUBECONFIG`
   - Value: The base64-encoded kubeconfig content
   - Click **Add secret**

#### Option B: Using Cloud Provider (Recommended for Production)

**For Google Cloud (GKE):**
```yaml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v2
  with:
    credentials_json: ${{ secrets.GCP_SA_KEY }}

- name: Set up Cloud SDK
  uses: google-github-actions/setup-gcloud@v2

- name: Configure kubectl
  run: |
    gcloud container clusters get-credentials CLUSTER_NAME --region REGION
```

**For Azure (AKS):**
```yaml
- name: Azure Login
  uses: azure/login@v1
  with:
    creds: ${{ secrets.AZURE_CREDENTIALS }}

- name: Set kubectl context
  uses: azure/aks-set-context@v3
  with:
    resource-group: RESOURCE_GROUP
    cluster-name: CLUSTER_NAME
```

**For AWS (EKS):**
```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: us-east-1

- name: Set kubectl context
  run: |
    aws eks update-kubeconfig --name CLUSTER_NAME --region REGION
```

### Step 4: Update Image References in Kubernetes Manifests

The CD workflow attempts to update image tags automatically, but you may need to adjust the deployment YAML files to use the correct image format.

Update `k8s/services/*-deployment.yaml` files to use:
```yaml
image: ghcr.io/YOUR_USERNAME/service-name:latest
```

Or use environment variables in your manifests.

### Step 5: Configure Environment Secrets (If Needed)

If your services require additional secrets, add them in GitHub:
- Go to **Settings** → **Secrets and variables** → **Actions**
- Add any required secrets (database passwords, API keys, etc.)

### Step 6: Test the Workflows

1. **Test CI**:
   - Create a new branch
   - Make a small change
   - Push to trigger CI
   - Create a Pull Request to see CI run

2. **Test CD**:
   - Merge to `main` branch (triggers automatic deployment)
   - Or use **Actions** tab → **CD - Deploy to Kubernetes** → **Run workflow**

## Workflow Customization

### Changing Image Registry

Edit `.github/workflows/ci.yml`:
```yaml
env:
  REGISTRY: docker.io  # or your registry
  IMAGE_PREFIX: your-username
```

### Changing Deployment Branch

Edit `.github/workflows/cd.yml`:
```yaml
on:
  push:
    branches: [ main, production ]  # Add your branches
```

### Adding More Test Steps

Add steps in the `test` job:
```yaml
- name: Run linting
  run: |
    pip install flake8 black
    flake8 .
    black --check .
```

### Conditional Deployment

Add conditions to deployment steps:
```yaml
- name: Deploy to Production
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  run: |
    # deployment commands
```

## Troubleshooting

### CI Workflow Issues

1. **Tests failing**: Check test output in Actions tab
2. **Docker build failing**: Verify Dockerfile syntax and dependencies
3. **Permission errors**: Ensure GitHub Actions has write permissions

### CD Workflow Issues

1. **kubectl connection failed**: 
   - Verify `KUBECONFIG` secret is correctly set
   - Check if the cluster is accessible from GitHub Actions runners

2. **Image pull errors**:
   - Ensure images are pushed to the registry
   - Check image pull secrets in Kubernetes

3. **Deployment timeout**:
   - Increase timeout values in the workflow
   - Check pod logs: `kubectl logs -n microservices <pod-name>`

## Security Best Practices

1. **Never commit secrets**: Always use GitHub Secrets
2. **Use least privilege**: Grant minimal permissions to service accounts
3. **Scan images**: Consider adding image vulnerability scanning
4. **Review deployments**: Use branch protection rules for production

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Kubernetes Deployment Best Practices](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)




