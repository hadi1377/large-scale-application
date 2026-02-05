# GitHub Actions CI/CD - Exact Setup Instructions

## ✅ What Has Been Created

I've added the following files to your project:

1. **`.github/workflows/ci.yml`** - Continuous Integration workflow
2. **`.github/workflows/cd.yml`** - Continuous Deployment workflow  
3. **`.github/workflows/README.md`** - Detailed technical documentation
4. **`GITHUB_ACTIONS_SETUP.md`** - Quick start guide
5. **`CI_CD_SETUP_INSTRUCTIONS.md`** - This file (step-by-step instructions)

## 🎯 How to Set It Up (Step-by-Step)

### Phase 1: Initial Setup (5 minutes)

#### Step 1: Commit and Push the Workflows

```bash
# Navigate to your project root
cd "H:\University\Arshad\5th Term\Large Scale\Project\source"

# Add the new GitHub Actions files
git add .github/
git add GITHUB_ACTIONS_SETUP.md
git add CI_CD_SETUP_INSTRUCTIONS.md

# Commit
git commit -m "Add GitHub Actions CI/CD workflows"

# Push to GitHub
git push origin main
```

#### Step 2: Verify Workflows Are Active

1. Open your GitHub repository in a web browser
2. Click on the **Actions** tab (top navigation)
3. You should see two workflows:
   - **CI - Test and Build**
   - **CD - Deploy to Kubernetes**
4. The CI workflow should automatically run on your push!

#### Step 3: Check CI Workflow Results

1. In the **Actions** tab, click on the latest workflow run
2. Watch it execute:
   - ✅ Tests run for each service
   - ✅ Docker images are built
   - ✅ Images are pushed to GitHub Container Registry

**If tests fail**: Check the logs to see which service failed and why.

### Phase 2: Configure Container Registry (Already Done!)

✅ **No action needed!** GitHub Container Registry works automatically.

Your images will be at:
- `ghcr.io/YOUR_GITHUB_USERNAME/api-gateway:latest`
- `ghcr.io/YOUR_GITHUB_USERNAME/user-service:latest`
- etc.

To view them:
- Go to your repository → **Packages** (right sidebar)

### Phase 3: Set Up Kubernetes Deployment (Required for CD)

#### Option A: Local/Minikube Setup (For Testing)

**Step 1: Get Your kubeconfig**

If using Minikube:
```powershell
# In PowerShell
minikube kubectl config view --flatten > kubeconfig.yaml
```

If using a local cluster:
```powershell
# Copy your existing kubeconfig
Copy-Item $env:USERPROFILE\.kube\config kubeconfig.yaml
```

**Step 2: Encode to Base64**

```powershell
# In PowerShell
$content = [IO.File]::ReadAllBytes("kubeconfig.yaml")
$base64 = [Convert]::ToBase64String($content)
$base64 | Out-File -Encoding ASCII kubeconfig-base64.txt
```

**Step 3: Add to GitHub Secrets**

1. Go to your GitHub repository
2. Click **Settings** (top right)
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret**
5. Name: `KUBECONFIG`
6. Value: Copy the entire content from `kubeconfig-base64.txt`
7. Click **Add secret**

**Step 4: Update Deployment Files (Important!)**

The deployment files currently use local image names. Update them to use the registry:

For each file in `k8s/services/*-deployment.yaml`, change:
```yaml
image: api-gateway:latest
```

To:
```yaml
image: ghcr.io/YOUR_GITHUB_USERNAME/api-gateway:latest
imagePullPolicy: Always
```

**Quick PowerShell script to update all:**
```powershell
$username = "YOUR_GITHUB_USERNAME"  # Replace with your GitHub username
$services = @("api-gateway", "user-service", "product-service", "order-service", "payment-service", "notification-service")

foreach ($service in $services) {
    $file = "k8s\services\$service-deployment.yaml"
    if (Test-Path $file) {
        (Get-Content $file) -replace "image: $service:latest", "image: ghcr.io/$username/$service:latest" | Set-Content $file
        (Get-Content $file) -replace "imagePullPolicy: IfNotPresent", "imagePullPolicy: Always" | Set-Content $file
        Write-Host "Updated $file"
    }
}
```

#### Option B: Cloud Provider Setup

See `.github/workflows/README.md` for detailed instructions for:
- Google Cloud (GKE)
- Azure (AKS)
- AWS (EKS)

### Phase 4: Test the Deployment

#### Test CI Workflow (Automatic)

1. Make a small change:
   ```bash
   echo "Test" >> README.md
   git add README.md
   git commit -m "Test CI"
   git push
   ```

2. Go to **Actions** tab and watch it run!

#### Test CD Workflow (Manual)

1. Go to **Actions** tab
2. Click **CD - Deploy to Kubernetes** (left sidebar)
3. Click **Run workflow** (right side)
4. Select:
   - Branch: `main`
   - Environment: `staging`
5. Click **Run workflow**
6. Watch the deployment!

#### Verify Deployment

After CD workflow completes:
```bash
# Check pods
kubectl get pods -n microservices

# Check services
kubectl get services -n microservices

# Check logs
kubectl logs -n microservices -l app=api-gateway
```

## 🔧 Customization Options

### Change Which Branches Trigger CD

Edit `.github/workflows/cd.yml`:
```yaml
on:
  push:
    branches: [ main, production ]  # Add your branches
```

### Use Docker Hub Instead

1. Edit `.github/workflows/ci.yml`:
   ```yaml
   env:
     REGISTRY: docker.io
     IMAGE_PREFIX: your-dockerhub-username
   ```

2. Add secrets:
   - `DOCKERHUB_USERNAME`
   - `DOCKERHUB_TOKEN`

### Add More Test Steps

Edit `.github/workflows/ci.yml` and add to the `test` job:
```yaml
- name: Run linting
  run: |
    pip install flake8 black
    flake8 .
    black --check .
```

## 🐛 Troubleshooting

### Workflow Not Running

**Problem**: Workflows don't appear or don't run

**Solution**:
1. Check if Actions are enabled: **Settings** → **Actions** → **General**
2. Ensure files are in `.github/workflows/` directory
3. Check YAML syntax (GitHub will show errors)

### Docker Build Fails

**Problem**: Images fail to build

**Solution**:
1. Check Actions logs for specific error
2. Test Dockerfile locally: `docker build -t test ./api-gateway`
3. Verify `requirements.txt` has all dependencies

### kubectl Connection Failed

**Problem**: CD workflow can't connect to Kubernetes

**Solution**:
1. Verify `KUBECONFIG` secret is set correctly
2. Test locally: `kubectl get nodes`
3. For cloud: ensure cluster is accessible from internet
4. Check if kubeconfig is base64 encoded correctly

### Image Pull Errors

**Problem**: Kubernetes can't pull images

**Solution**:
1. Verify images exist: Go to **Packages** tab
2. Check image name matches in deployment YAML
3. For private registry, add image pull secrets:
   ```yaml
   imagePullSecrets:
   - name: ghcr-secret
   ```

### Tests Failing

**Problem**: CI tests fail

**Solution**:
1. Run tests locally: `python run_tests.py`
2. Check specific service logs in Actions
3. Fix failing tests before merging

## 📊 Monitoring Workflows

### View Workflow Status

- **Actions** tab shows all workflow runs
- Green checkmark = success
- Red X = failure
- Yellow circle = in progress

### View Logs

1. Click on a workflow run
2. Click on a job (e.g., "Run Tests")
3. Click on a step to see detailed logs

### Set Up Notifications

1. Go to **Settings** → **Notifications**
2. Enable email notifications for workflow failures
3. Or integrate with Slack/Discord

## ✅ Success Checklist

- [ ] Workflows pushed to GitHub
- [ ] CI workflow runs on push/PR
- [ ] All tests pass
- [ ] Docker images build successfully
- [ ] Images appear in Packages tab
- [ ] `KUBECONFIG` secret added (for CD)
- [ ] Deployment files updated with registry images
- [ ] CD workflow can connect to Kubernetes
- [ ] Deployment succeeds
- [ ] Services are running in Kubernetes

## 🎓 Next Steps

1. **Add branch protection**: Require CI to pass before merging
2. **Set up environments**: Create staging/production environments
3. **Add monitoring**: Set up alerts for deployment failures
4. **Improve tests**: Add integration tests, load tests
5. **Security scanning**: Add vulnerability scanning for images

## 📚 Additional Resources

- Quick Start: `GITHUB_ACTIONS_SETUP.md`
- Detailed Docs: `.github/workflows/README.md`
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

---

**Need Help?** Check the Actions tab logs - they show exactly what went wrong!

