# Accessing Management UIs in Minikube

Quick reference guide for accessing RabbitMQ Management UI and Mailpit Web UI in your Kubernetes cluster.

---

## 🚀 Quick Access (Port Forwarding - Recommended)

This is the easiest and most reliable method for Minikube:

### API Gateway (Main Application)
```bash
kubectl port-forward -n microservices svc/api-gateway 8050:8000
```
**Access**: http://localhost:8050

---

### RabbitMQ Management UI
```bash
kubectl port-forward -n microservices svc/rabbitmq 15672:15672
```
**Access**: http://localhost:15672

**Login Credentials:**
- Username: `rabbitmq_user`
- Password: `rabbitmq_password`

**What you can do:**
- ✅ Monitor queues and messages
- ✅ View connections and channels
- ✅ Manage exchanges and bindings
- ✅ See message rates and statistics
- ✅ Debug message flow between services

---

### Mailpit Web UI
```bash
kubectl port-forward -n microservices svc/mailpit 8025:8025
```
**Access**: http://localhost:8025

**What you can do:**
- ✅ View all emails sent by your services
- ✅ Test email templates
- ✅ Debug notification workflows
- ✅ No authentication required

---

## 🌐 Access via Ingress (Alternative Method)

If you prefer to access everything through the Ingress controller:

### Step 1: Get Minikube IP
```bash
minikube ip
```

Example output: `192.168.49.2`

### Step 2: Add to Hosts File

**Windows:**
Open `C:\Windows\System32\drivers\etc\hosts` as Administrator and add:
```
192.168.49.2  microservices.local
```

**Linux/Mac:**
```bash
sudo nano /etc/hosts
# Add this line:
192.168.49.2  microservices.local
```

### Step 3: Access Services

- **API Gateway**: http://microservices.local/
- **RabbitMQ**: http://microservices.local/rabbitmq
- **Mailpit**: http://microservices.local/mailpit

**Or use IP directly (without hosts file):**
- **API Gateway**: http://192.168.49.2/
- **RabbitMQ**: http://192.168.49.2/rabbitmq
- **Mailpit**: http://192.168.49.2/mailpit

---

## 📋 All Available Endpoints

### Via Port Forward (Localhost)

| Service | Command | URL | Credentials |
|---------|---------|-----|-------------|
| API Gateway | `kubectl port-forward -n microservices svc/api-gateway 8050:8000` | http://localhost:8050 | None |
| RabbitMQ UI | `kubectl port-forward -n microservices svc/rabbitmq 15672:15672` | http://localhost:15672 | rabbitmq_user / rabbitmq_password |
| Mailpit UI | `kubectl port-forward -n microservices svc/mailpit 8025:8025` | http://localhost:8025 | None |
| User Service | `kubectl port-forward -n microservices svc/user-service 8001:8000` | http://localhost:8001 | JWT Token |
| Product Service | `kubectl port-forward -n microservices svc/product-service 8002:8000` | http://localhost:8002 | None |
| Order Service | `kubectl port-forward -n microservices svc/order-service 8003:8000` | http://localhost:8003 | JWT Token |
| Payment Service | `kubectl port-forward -n microservices svc/payment-service 8004:8000` | http://localhost:8004 | API Key |

### Via Ingress (microservices.local)

| Service | URL | Credentials |
|---------|-----|-------------|
| API Gateway | http://microservices.local/ | None |
| RabbitMQ UI | http://microservices.local/rabbitmq | rabbitmq_user / rabbitmq_password |
| Mailpit UI | http://microservices.local/mailpit | None |
| User API | http://microservices.local/api/user-service/* | JWT Token |
| Product API | http://microservices.local/api/product-service/* | None |
| Order API | http://microservices.local/api/order-service/* | JWT Token |
| Payment API | http://microservices.local/api/payment-service/* | API Key |

---

## 💡 Pro Tips

### Run Multiple Port Forwards Simultaneously

**Method 1: Multiple Terminals**
Open separate terminal windows for each service.

**Method 2: Background Jobs (PowerShell)**
```powershell
# Start background jobs
Start-Job -ScriptBlock { kubectl port-forward -n microservices svc/api-gateway 8050:8000 }
Start-Job -ScriptBlock { kubectl port-forward -n microservices svc/rabbitmq 15672:15672 }
Start-Job -ScriptBlock { kubectl port-forward -n microservices svc/mailpit 8025:8025 }

# View running jobs
Get-Job

# Stop all jobs when done
Get-Job | Stop-Job
Get-Job | Remove-Job
```

**Method 3: Background Jobs (Linux/Mac)**
```bash
# Start in background
kubectl port-forward -n microservices svc/api-gateway 8050:8000 &
kubectl port-forward -n microservices svc/rabbitmq 15672:15672 &
kubectl port-forward -n microservices svc/mailpit 8025:8025 &

# View background jobs
jobs

# Bring to foreground (replace %1 with job number)
fg %1

# Kill all background kubectl processes
killall kubectl
```

### Create Aliases for Quick Access

**PowerShell** (add to your profile):
```powershell
function Start-Microservices {
    Start-Job -ScriptBlock { kubectl port-forward -n microservices svc/api-gateway 8050:8000 }
    Start-Job -ScriptBlock { kubectl port-forward -n microservices svc/rabbitmq 15672:15672 }
    Start-Job -ScriptBlock { kubectl port-forward -n microservices svc/mailpit 8025:8025 }
    Write-Host "Services started! Access at:" -ForegroundColor Green
    Write-Host "  API Gateway: http://localhost:8050" -ForegroundColor Cyan
    Write-Host "  RabbitMQ: http://localhost:15672" -ForegroundColor Cyan
    Write-Host "  Mailpit: http://localhost:8025" -ForegroundColor Cyan
}

function Stop-Microservices {
    Get-Job | Stop-Job
    Get-Job | Remove-Job
    Write-Host "All services stopped!" -ForegroundColor Yellow
}
```

**Bash/Zsh** (add to ~/.bashrc or ~/.zshrc):
```bash
alias k8s-start='kubectl port-forward -n microservices svc/api-gateway 8050:8000 & kubectl port-forward -n microservices svc/rabbitmq 15672:15672 & kubectl port-forward -n microservices svc/mailpit 8025:8025 &'
alias k8s-stop='killall kubectl'
```

---

## 🔍 Troubleshooting

### Port Forward Fails

**Check if pods are running:**
```bash
kubectl get pods -n microservices
```

**Check specific service:**
```bash
kubectl get svc rabbitmq -n microservices
kubectl describe svc rabbitmq -n microservices
```

**View pod logs:**
```bash
# RabbitMQ
kubectl logs -n microservices $(kubectl get pod -n microservices -l app=rabbitmq -o jsonpath='{.items[0].metadata.name}')

# Mailpit
kubectl logs -n microservices $(kubectl get pod -n microservices -l app=mailpit -o jsonpath='{.items[0].metadata.name}')
```

### Can't Access via Ingress

**Check Ingress status:**
```bash
kubectl get ingress -n microservices
kubectl describe ingress microservices-ingress -n microservices
kubectl describe ingress rabbitmq-ingress -n microservices
kubectl describe ingress mailpit-ingress -n microservices
```

**Verify Ingress controller:**
```bash
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller
```

**Test Ingress directly:**
```bash
curl -H "Host: microservices.local" http://$(minikube ip)/
curl -H "Host: microservices.local" http://$(minikube ip)/rabbitmq
curl -H "Host: microservices.local" http://$(minikube ip)/mailpit
```

### RabbitMQ UI Not Loading Properly

If the RabbitMQ UI loads but assets are missing:
1. Use port-forward method instead (recommended for Minikube)
2. Check if the Ingress rewrite rules are working:
   ```bash
   kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller --tail=50
   ```

### Mailpit Shows No Emails

**Trigger a test email:**
1. Create an order through the Order Service
2. Check notification service logs:
   ```bash
   kubectl logs -n microservices -l app=notification-service -f
   ```
3. Verify RabbitMQ shows the message:
   - Go to http://localhost:15672
   - Check Queues tab for messages

---

## 🎯 Common Use Cases

### Monitor Order Processing Flow

1. **Open RabbitMQ UI**: http://localhost:15672
2. **Open Mailpit UI**: http://localhost:8025
3. **Create an order** via API Gateway: http://localhost:8050
4. Watch:
   - RabbitMQ: See message published to queue
   - Mailpit: See order confirmation email arrive

### Debug Email Templates

1. **Access Mailpit**: http://localhost:8025
2. **Trigger notifications** via Order Service
3. **View email HTML/text** in Mailpit
4. **Test different scenarios** (order placed, completed, failed)

### Monitor System Health

1. **RabbitMQ**: Check message rates and queue depths
2. **Mailpit**: Verify email delivery
3. **API Gateway**: Monitor service availability at http://localhost:8050/health

---

## 📚 Additional Resources

- **RabbitMQ Management UI Docs**: https://www.rabbitmq.com/management.html
- **Mailpit GitHub**: https://github.com/axllent/mailpit
- **Kubernetes Port Forwarding**: https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/

---

**Recommended**: For Minikube development, use **port-forwarding** for the most reliable access to RabbitMQ and Mailpit UIs! 🚀




