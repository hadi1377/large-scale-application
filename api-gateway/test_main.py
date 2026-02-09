import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import json

from main import app, SERVICES


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_service_response():
    """Mock service response"""
    return {"service": "test-service", "status": "ok"}


@pytest.mark.asyncio
class TestRootEndpoint:
    """Test root endpoint"""
    
    async def test_root(self, client):
        """Test root endpoint returns HTML"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "API Gateway" in response.text
        assert "User Service" in response.text
        assert "Product Service" in response.text


@pytest.mark.asyncio
class TestHealthEndpoints:
    """Test health check endpoints"""
    
    async def test_health(self, client):
        """Test main health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "api-gateway"
    
    @patch('main.httpx.AsyncClient')
    async def test_service_health_success(self, mock_client_class, client, mock_service_response):
        """Test service health check success"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_service_response
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        response = client.get("/health/user-service")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "user-service"
        assert data["status"] == "healthy"
    
    @patch('main.httpx.AsyncClient')
    async def test_service_health_timeout(self, mock_client_class, client):
        """Test service health check timeout"""
        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=Exception("Timeout"))
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        import httpx
        with patch('main.httpx.TimeoutException', Exception):
            response = client.get("/health/user-service")
            assert response.status_code in [500, 504]
    
    async def test_service_health_invalid_service(self, client):
        """Test health check for invalid service"""
        response = client.get("/health/invalid-service")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestOpenAPIEndpoints:
    """Test OpenAPI endpoints"""
    
    @patch('main.httpx.AsyncClient')
    async def test_get_service_openapi_success(self, mock_client_class, client):
        """Test getting OpenAPI JSON successfully"""
        mock_openapi = {
            "openapi": "3.0.2",
            "info": {"title": "Test Service", "version": "1.0.0"},
            "paths": {}
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openapi
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        response = client.get("/openapi.json/user-service")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert "openapi" in data
        assert "servers" in data
    
    @patch('main.httpx.AsyncClient')
    async def test_get_service_openapi_not_found(self, mock_client_class, client):
        """Test getting OpenAPI when service not found"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        response = client.get("/openapi.json/user-service")
        assert response.status_code == 404
    
    async def test_get_service_openapi_invalid_service(self, client):
        """Test getting OpenAPI for invalid service"""
        response = client.get("/openapi.json/invalid-service")
        assert response.status_code == 404
    
    @patch('main.httpx.AsyncClient')
    async def test_get_service_docs(self, mock_client_class, client):
        """Test getting service docs page"""
        mock_openapi = {
            "openapi": "3.0.2",
            "info": {"title": "Test Service", "version": "1.0.0"},
            "paths": {}
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openapi
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        response = client.get("/docs/user-service")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    async def test_get_service_docs_invalid_service(self, client):
        """Test getting docs for invalid service"""
        response = client.get("/docs/invalid-service")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestProxyEndpoints:
    """Test proxy endpoints"""
    
    @patch('main.httpx.AsyncClient')
    async def test_proxy_get_success(self, mock_client_class, client, mock_service_response):
        """Test successful GET proxy request"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(mock_service_response).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        response = client.get("/api/user-service/test")
        assert response.status_code == 200
        data = response.json()
        assert data == mock_service_response
    
    @patch('main.httpx.AsyncClient')
    async def test_proxy_post_success(self, mock_client_class, client):
        """Test successful POST proxy request"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.content = b'{"id": "123"}'
        mock_response.headers = {"content-type": "application/json"}
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        response = client.post(
            "/api/user-service/register",
            json={"email": "test@example.com", "password": "pass", "full_name": "Test"}
        )
        assert response.status_code == 201
    
    @patch('main.httpx.AsyncClient')
    async def test_proxy_put_success(self, mock_client_class, client):
        """Test successful PUT proxy request"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"updated": true}'
        mock_response.headers = {"content-type": "application/json"}
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        response = client.put(
            "/api/product-service/products/123",
            json={"name": "Updated Product"}
        )
        assert response.status_code == 200
    
    @patch('main.httpx.AsyncClient')
    async def test_proxy_delete_success(self, mock_client_class, client):
        """Test successful DELETE proxy request"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.content = b''
        mock_response.headers = {}
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        response = client.delete("/api/product-service/products/123")
        assert response.status_code == 204
    
    async def test_proxy_invalid_service(self, client):
        """Test proxy request to invalid service"""
        response = client.get("/api/invalid-service/test")
        assert response.status_code == 404
    
    @patch('main.httpx.AsyncClient')
    async def test_proxy_timeout(self, mock_client_class, client):
        """Test proxy request timeout"""
        import httpx
        mock_client = MagicMock()
        mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        response = client.get("/api/user-service/test")
        assert response.status_code == 504
    
    @patch('main.httpx.AsyncClient')
    async def test_proxy_connection_error(self, mock_client_class, client):
        """Test proxy request connection error"""
        import httpx
        mock_client = MagicMock()
        mock_client.request = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        response = client.get("/api/user-service/test")
        assert response.status_code == 503
    
    @patch('main.httpx.AsyncClient')
    async def test_proxy_with_query_params(self, mock_client_class, client):
        """Test proxy request with query parameters"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'[]'
        mock_response.headers = {"content-type": "application/json"}
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        response = client.get("/api/product-service/products?skip=0&limit=10")
        assert response.status_code == 200
        # Verify query params were passed
        call_args = mock_client.request.call_args
        assert "params" in call_args.kwargs or "skip=0" in str(call_args)


@pytest.mark.asyncio
class TestServiceConstants:
    """Test service constants"""
    
    async def test_services_defined(self):
        """Test that all services are defined"""
        assert "user-service" in SERVICES
        assert "product-service" in SERVICES
        assert "order-service" in SERVICES
        assert "payment-service" in SERVICES
        assert "notification-service" in SERVICES




