# k6 Load Testing - Quick Start

## Installation

### Windows
```powershell
# Using Chocolatey
choco install k6

# Or download from https://k6.io/docs/getting-started/installation/
```

### macOS
```bash
brew install k6
```

### Linux
```bash
# Debian/Ubuntu
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D9B
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

## Quick Test

1. **Start your application** (API Gateway should be accessible)

2. **Run a smoke test**:
   ```bash
   # Windows PowerShell
   cd k6
   .\run-tests.ps1 smoke
   
   # Linux/macOS
   cd k6
   chmod +x run-tests.sh
   ./run-tests.sh smoke
   
   # Or directly with k6
   k6 run scenarios/smoke.js
   ```

3. **Run with custom URL**:
   ```bash
   # Windows PowerShell
   $env:BASE_URL="http://your-url:port"; k6 run scenarios/smoke.js
   
   # Linux/macOS
   BASE_URL=http://your-url:port k6 run scenarios/smoke.js
   ```

## Available Tests

| Test | Command | Duration | Purpose |
|------|---------|----------|---------|
| **Smoke** | `k6 run scenarios/smoke.js` | ~30s | Quick validation |
| **Load** | `k6 run scenarios/load.js` | ~9m | Normal load |
| **Stress** | `k6 run scenarios/stress.js` | ~23m | System limits |
| **Spike** | `k6 run scenarios/spike.js` | ~4m | Traffic spikes |
| **E2E** | `k6 run scenarios/e2e.js` | ~5m | Full user journey |

## Common Issues

### Connection Refused
- Ensure API Gateway is running
- Check port forwarding: `kubectl port-forward -n microservices svc/api-gateway 8050:8000`
- Verify BASE_URL is correct

### High Failure Rate
- Check if all services are running
- Review service logs
- Reduce load and retry

For more details, see [README.md](README.md)




