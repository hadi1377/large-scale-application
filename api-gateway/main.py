from fastapi import FastAPI, Response, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from prometheus_fastapi_instrumentator import Instrumentator
import httpx
import json

app = FastAPI(
    title="API Gateway - All Services Documentation",
    description="Centralized API documentation for all microservices",
    version="1.0.0"
)

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Service URLs (adjust ports as needed)
SERVICES = {
    "user-service": "http://user-service:8000",
    "product-service": "http://product-service:8000",
    "order-service": "http://order-service:8000",
    "payment-service": "http://payment-service:8000",
    "notification-service": "http://notification-service:8000",
}


@app.get("/", response_class=HTMLResponse)
async def root():
    """Main documentation page with links to all services."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Gateway - All Services</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            h1 {
                color: #333;
                border-bottom: 3px solid #4CAF50;
                padding-bottom: 10px;
            }
            .service-card {
                background: white;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border-left: 4px solid #4CAF50;
            }
            .service-card h2 {
                margin-top: 0;
                color: #4CAF50;
            }
            .service-link {
                display: inline-block;
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 4px;
                margin-top: 10px;
            }
            .service-link:hover {
                background-color: #45a049;
            }
            .description {
                color: #666;
                margin: 10px 0;
            }
        </style>
    </head>
    <body>
        <h1>🚀 API Gateway - All Services Documentation</h1>
        <p>Select a service to view its API documentation:</p>
        
        <div class="service-card">
            <h2>👤 User Service</h2>
            <p class="description">User management, registration, and authentication</p>
            <a href="/docs/user-service" class="service-link">View User Service Docs</a>
            <a href="/openapi.json/user-service" class="service-link" style="background-color: #2196F3; margin-left: 10px;">OpenAPI JSON</a>
        </div>
        
        <div class="service-card">
            <h2>📦 Product Service</h2>
            <p class="description">Product catalog and management</p>
            <a href="/docs/product-service" class="service-link">View Product Service Docs</a>
            <a href="/openapi.json/product-service" class="service-link" style="background-color: #2196F3; margin-left: 10px;">OpenAPI JSON</a>
        </div>
        
        <div class="service-card">
            <h2>🛒 Order Service</h2>
            <p class="description">Order processing and management</p>
            <a href="/docs/order-service" class="service-link">View Order Service Docs</a>
            <a href="/openapi.json/order-service" class="service-link" style="background-color: #2196F3; margin-left: 10px;">OpenAPI JSON</a>
        </div>
        
        <div class="service-card">
            <h2>💳 Payment Service</h2>
            <p class="description">Payment processing and transactions</p>
            <a href="/docs/payment-service" class="service-link">View Payment Service Docs</a>
            <a href="/openapi.json/payment-service" class="service-link" style="background-color: #2196F3; margin-left: 10px;">OpenAPI JSON</a>
        </div>
        
        <div class="service-card">
            <h2>🔔 Notification Service</h2>
            <p class="description">Notifications and messaging</p>
            <a href="/docs/notification-service" class="service-link">View Notification Service Docs</a>
            <a href="/openapi.json/notification-service" class="service-link" style="background-color: #2196F3; margin-left: 10px;">OpenAPI JSON</a>
        </div>
    </body>
    </html>
    """
    return html_content


@app.get("/openapi.json/{service_name}")
async def get_service_openapi(service_name: str):
    """Fetch OpenAPI JSON from a specific service."""
    if service_name not in SERVICES:
        return JSONResponse(
            status_code=404,
            content={"error": f"Service '{service_name}' not found"}
        )
    
    service_url = SERVICES[service_name]
    timeout = httpx.Timeout(30.0, connect=10.0)  # 30s total, 10s for connection
    
    # Retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(f"{service_url}/openapi.json")
                if response.status_code == 200:
                    openapi_data = response.json()
                    # Ensure openapi version field exists (FastAPI should include it, but ensure it's there)
                    if "openapi" not in openapi_data and "swagger" not in openapi_data:
                        # If missing, add OpenAPI 3.0.2 (FastAPI default)
                        openapi_data["openapi"] = "3.0.2"
                    # Update servers field to point to the proxy endpoint
                    openapi_data["servers"] = [{"url": f"/api/{service_name}", "description": f"{service_name} API"}]
                    # Return as proper JSON response with correct content type
                    return Response(
                        content=json.dumps(openapi_data, indent=2),
                        media_type="application/json"
                    )
                else:
                    error_msg = f"Failed to fetch OpenAPI from {service_name}: HTTP {response.status_code}"
                    if attempt < max_retries - 1:
                        continue  # Retry
                    return JSONResponse(
                        status_code=response.status_code,
                        content={"error": error_msg, "details": response.text[:200]}
                    )
        except httpx.TimeoutException:
            if attempt < max_retries - 1:
                continue  # Retry
            return JSONResponse(
                status_code=504,
                content={"error": f"Timeout connecting to {service_name} after {max_retries} attempts. Make sure the service is running."}
            )
        except httpx.ConnectError as e:
            if attempt < max_retries - 1:
                continue  # Retry
            return JSONResponse(
                status_code=503,
                content={"error": f"Cannot connect to {service_name}. Service may not be running.", "details": str(e)}
            )
        except Exception as e:
            if attempt < max_retries - 1:
                continue  # Retry
            return JSONResponse(
                status_code=500,
                content={"error": f"Error connecting to {service_name}: {str(e)}"}
            )
    
    return JSONResponse(
        status_code=500,
        content={"error": f"Failed to fetch OpenAPI from {service_name} after {max_retries} attempts"}
    )


@app.get("/docs/{service_name}", response_class=HTMLResponse)
async def get_service_docs(service_name: str):
    """Display Swagger UI for a specific service."""
    if service_name not in SERVICES:
        return HTMLResponse("<h1>Service not found</h1>", status_code=404)
    
    service_url = SERVICES[service_name]
    openapi_url = f"/openapi.json/{service_name}"
    
    return get_swagger_ui_html(
        openapi_url=openapi_url,
        title=f"{service_name.replace('-', ' ').title()} API Documentation",
        swagger_ui_parameters={"persistAuthorization": True}
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "api-gateway"}


@app.get("/health/{service_name}")
async def check_service_health(service_name: str):
    """Check if a specific service is accessible."""
    if service_name not in SERVICES:
        return JSONResponse(
            status_code=404,
            content={"error": f"Service '{service_name}' not found"}
        )
    
    service_url = SERVICES[service_name]
    timeout = httpx.Timeout(5.0, connect=2.0)
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Try to reach the root endpoint
            response = await client.get(f"{service_url}/", timeout=timeout)
            return {
                "service": service_name,
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "url": service_url
            }
    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content={"service": service_name, "status": "timeout", "url": service_url}
        )
    except httpx.ConnectError:
        return JSONResponse(
            status_code=503,
            content={"service": service_name, "status": "unreachable", "url": service_url}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"service": service_name, "status": "error", "error": str(e)}
        )


@app.api_route("/api/{service_name}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
@app.api_route("/api/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_request(service_name: str, request: Request, path: str = ""):
    """Proxy requests to the appropriate service."""
    if service_name not in SERVICES:
        return JSONResponse(
            status_code=404,
            content={"error": f"Service '{service_name}' not found"}
        )
    
    service_url = SERVICES[service_name]
    # Construct target URL - handle empty path for root endpoints
    if path:
        target_url = f"{service_url}/{path}"
    else:
        target_url = service_url
    
    # Get query parameters
    query_params = dict(request.query_params)
    
    # Get request body if present
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
    
    # Get headers (exclude host and connection headers)
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("connection", None)
    
    timeout = httpx.Timeout(30.0, connect=10.0)
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                params=query_params,
                content=body,
                headers=headers,
                follow_redirects=True
            )
            
            # Return response with proper headers
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content={"error": f"Timeout connecting to {service_name}"}
        )
    except httpx.ConnectError:
        return JSONResponse(
            status_code=503,
            content={"error": f"Cannot connect to {service_name}. Service may not be running."}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error proxying request to {service_name}: {str(e)}"}
        )

