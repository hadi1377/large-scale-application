# GitHub Actions CI/CD Quick Setup Guide

This guide will help you set up CI/CD for your microservices project in under 10 minutes.

## 🚀 Quick Start (5 Steps)

### Step 1: Push the Workflows to GitHub

The workflows are already in `.github/workflows/`. Just commit and push:

```bash
git add .github/
git commit -m "Add GitHub Actions CI/CD workflows"
git push origin main
```

### Step 2: Verify Workflows Are Active

1. Go to your GitHub repository
2. Click on the **Actions** tab
3. You should see the workflows listed
4. The CI workflow will run automatically on your next push/PR

### Step 3: Configure Container Registry (Automatic)

✅ **Good news**: GitHub Container Registry (ghcr.io) works automatically with `GITHUB_TOKEN` - no setup needed!

Your images will be available at:
- `ghcr.io/YOUR_USERNAME/api-gateway:latest`
- `ghcr.io/YOUR_USERNAME/user-service:latest`
- etc.

To view your images:
1. Go to your GitHub repository
2. Click **Packages** (on the right sidebar)
3. You'll see all your container images

### Step 4: Set Up Kubernetes Access (For Deployment)

#### For Local Testing (Minikube/Kind):

1. **Get your kubeconfig:**
   ```bash
   # If using Minikube
   minikube kubectl config view --flatten > kubeconfig.yaml
   ```

2. **Encode to base64:**
   ```bash
   # Linux/Mac
   base64 -i kubeconfig.yaml
   
   # Windows PowerShell
   [Convert]::ToBase64String([IO.File]::ReadAllBytes("kubeconfig.yaml"))
   ```

3. **Add to GitHub Secrets:**
   - Repository → **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `KUBECONFIG`
   - Value: Paste the base64 output
   - Click **Add secret**

#### For Cloud Providers:

See detailed instructions in `.github/workflows/README.md`

### Step 5: Test It!

1. **Test CI (automatic):**
   ```bash
   # Make a small change
   echo "# Test" >> README.md
   git add README.md
   git commit -m "Test CI workflow"
   git push
   ```
   
   Check the **Actions** tab to see it running!

2. **Test CD (manual):**
   - Go to **Actions** tab
   - Select **CD - Deploy to Kubernetes**
   - Click **Run workflow**
   - Choose branch and environment
   - Click **Run workflow**

## 📋 What Each Workflow Does

### CI Workflow (`ci.yml`)
- ✅ Runs tests for all 6 microservices
- ✅ Builds Docker images
- ✅ Pushes images to GitHub Container Registry
- ✅ Runs on every push and pull request

### CD Workflow (`cd.yml`)
- 🚀 Deploys to Kubernetes
- 🚀 Updates all services
- 🚀 Only runs on `main`/`master` branch or tags
- 🚀 Can be triggered manually

## 🔧 Common Customizations

### Change Image Registry to Docker Hub

1. Edit `.github/workflows/ci.yml`:
   ```yaml
   env:
     REGISTRY: docker.io
     IMAGE_PREFIX: your-dockerhub-username
   ```

2. Add secrets:
   - `DOCKERHUB_USERNAME`: Your Docker Hub username
   - `DOCKERHUB_TOKEN`: Your Docker Hub access token

### Skip Deployment for Certain Branches

Edit `.github/workflows/cd.yml`:
```yaml
on:
  push:
    branches: [ main ]  # Only deploy from main
```

### Add Environment-Specific Deployments

The CD workflow already supports environments via `workflow_dispatch`. You can add more:

```yaml
environment: ${{ github.event.inputs.environment || 'staging' }}
```

Then create environment-specific secrets in GitHub Settings.

## 🐛 Troubleshooting

### "Workflow not running"
- Check if Actions are enabled: **Settings** → **Actions** → **General**
- Ensure workflows are in `.github/workflows/` directory

### "Docker build failed"
- Check Dockerfile syntax
- Verify all dependencies in `requirements.txt`
- Check Actions logs for specific error

### "kubectl connection failed"
- Verify `KUBECONFIG` secret is set correctly
- Test kubeconfig locally: `kubectl get nodes`
- For cloud: ensure cluster is accessible from internet

### "Image pull error in Kubernetes"
- Check if images exist: Go to **Packages** tab
- Verify image name matches in deployment YAML
- Add image pull secrets if using private registry

## 📚 Next Steps

1. **Add branch protection rules:**
   - Require CI to pass before merging
   - Require reviews for production deployments

2. **Set up notifications:**
   - GitHub will email you on workflow failures
   - Or integrate with Slack/Discord

3. **Add more checks:**
   - Code linting (flake8, black)
   - Security scanning (Snyk, Trivy)
   - Integration tests

4. **Monitor deployments:**
   - Set up Kubernetes monitoring
   - Add health check endpoints
   - Configure alerts

## 📖 Detailed Documentation

For advanced configuration, see:
- `.github/workflows/README.md` - Complete setup guide
- [GitHub Actions Docs](https://docs.github.com/en/actions)

## ✅ Checklist

- [ ] Workflows pushed to GitHub
- [ ] CI workflow runs successfully
- [ ] Docker images build and push correctly
- [ ] `KUBECONFIG` secret added (for CD)
- [ ] CD workflow can connect to Kubernetes
- [ ] Deployment succeeds
- [ ] Services are accessible after deployment

---

**Need Help?** Check the Actions tab logs for detailed error messages!

