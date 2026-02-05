import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from contextlib import asynccontextmanager
import json
import uuid

from main import app
from email_service import (
    get_user_email,
    get_email_subject,
    get_email_body,
    send_email,
    send_order_notification
)
from rabbitmq_consumer import process_message, SUPPORTED_EVENTS


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_order_data():
    """Sample order data for testing"""
    return {
        "order_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "status": "pending",
        "total_amount": "99.99"
    }


class TestEmailService:
    """Test email service functions"""
    
    @pytest.mark.asyncio
    @patch('email_service.call_user_service')
    async def test_get_user_email_success(self, mock_call_user_service):
        """Test getting user email successfully"""
        user_id = str(uuid.uuid4())
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"email": "test@example.com"}
        mock_call_user_service.return_value = mock_response
        
        email = await get_user_email(user_id)
        assert email == "test@example.com"
    
    @pytest.mark.asyncio
    @patch('email_service.call_user_service')
    async def test_get_user_email_not_found(self, mock_call_user_service):
        """Test getting user email when user not found"""
        user_id = str(uuid.uuid4())
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_call_user_service.return_value = mock_response
        
        email = await get_user_email(user_id)
        assert email == ""
    
    @pytest.mark.asyncio
    @patch('email_service.call_user_service')
    async def test_get_user_email_service_unavailable(self, mock_call_user_service):
        """Test getting user email when service is unavailable"""
        user_id = str(uuid.uuid4())
        mock_call_user_service.side_effect = Exception("Service unavailable")
        
        email = await get_user_email(user_id)
        assert email == ""
    
    # Remove @pytest.mark.asyncio from non-async functions
    def test_get_email_subject(self):
        """Test email subject generation"""
        assert get_email_subject("order_placed") == "Order Placed Successfully"
        assert get_email_subject("order_failed") == "Order Failed"
        assert get_email_subject("order_completed") == "Order Completed"
        assert get_email_subject("unknown") == "Order Update"
    
    def test_get_email_body_order_placed(self, sample_order_data):
        """Test email body for order placed"""
        body = get_email_body("order_placed", sample_order_data)
        assert "Order Placed Successfully" in body
        assert sample_order_data["order_id"] in body
        assert sample_order_data["total_amount"] in body
    
    def test_get_email_body_order_failed(self, sample_order_data):
        """Test email body for order failed"""
        body = get_email_body("order_failed", sample_order_data)
        assert "Order Failed" in body
        assert sample_order_data["order_id"] in body
    
    def test_get_email_body_order_completed(self, sample_order_data):
        """Test email body for order completed"""
        body = get_email_body("order_completed", sample_order_data)
        assert "Order Completed" in body
        assert sample_order_data["order_id"] in body
    
    @pytest.mark.asyncio
    @patch('email_service.aiosmtplib.send')
    async def test_send_email_success(self, mock_send):
        """Test successful email sending"""
        mock_send.return_value = None
        
        result = await send_email("test@example.com", "Test Subject", "<html><body>Test</body></html>")
        assert result is True
        mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('email_service.aiosmtplib.send')
    async def test_send_email_failure(self, mock_send):
        """Test email sending failure"""
        mock_send.side_effect = Exception("SMTP Error")
        
        result = await send_email("test@example.com", "Test Subject", "<html><body>Test</body></html>")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_email_empty_recipient(self):
        """Test email sending with empty recipient"""
        result = await send_email("", "Test Subject", "<html><body>Test</body></html>")
        assert result is False
    
    @pytest.mark.asyncio
    @patch('email_service.send_email')
    @patch('email_service.get_user_email')
    async def test_send_order_notification_success(
        self,
        mock_get_user_email,
        mock_send_email,
        sample_order_data
    ):
        """Test successful order notification"""
        mock_get_user_email.return_value = "test@example.com"
        mock_send_email.return_value = True
        
        result = await send_order_notification("order_placed", sample_order_data)
        assert result is True
        mock_get_user_email.assert_called_once()
        mock_send_email.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('email_service.get_user_email')
    async def test_send_order_notification_no_user_id(self, mock_get_user_email):
        """Test order notification without user_id"""
        result = await send_order_notification("order_placed", {})
        assert result is False
    
    @pytest.mark.asyncio
    @patch('email_service.get_user_email')
    async def test_send_order_notification_user_not_found(
        self,
        mock_get_user_email,
        sample_order_data
    ):
        """Test order notification when user not found"""
        mock_get_user_email.return_value = ""
        
        result = await send_order_notification("order_placed", sample_order_data)
        assert result is False


class TestRabbitMQConsumer:
    """Test RabbitMQ consumer functions"""
    
    @pytest.mark.asyncio
    async def test_process_message_order_placed(self, sample_order_data):
        """Test processing order_placed message"""
        message_body = json.dumps({
            "event_type": "order_placed",
            "order_data": sample_order_data
        })
        
        # Create a proper async context manager mock
        @asynccontextmanager
        async def mock_process():
            yield
        
        mock_message = MagicMock()
        mock_message.body = message_body.encode()
        mock_message.process = mock_process
        
        with patch('rabbitmq_consumer.send_order_notification', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            async with mock_message.process():
                await process_message(mock_message)
            
            mock_send.assert_called_once_with("order_placed", sample_order_data)
    
    @pytest.mark.asyncio
    async def test_process_message_unsupported_event(self):
        """Test processing unsupported event"""
        message_body = json.dumps({
            "event_type": "unsupported_event",
            "order_data": {}
        })
        
        # Create a proper async context manager mock
        @asynccontextmanager
        async def mock_process():
            yield
        
        mock_message = MagicMock()
        mock_message.body = message_body.encode()
        mock_message.process = mock_process
        
        with patch('rabbitmq_consumer.send_order_notification', new_callable=AsyncMock) as mock_send:
            async with mock_message.process():
                await process_message(mock_message)
            
            mock_send.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_message_invalid_json(self):
        """Test processing message with invalid JSON"""
        # Create a proper async context manager mock
        @asynccontextmanager
        async def mock_process():
            yield
        
        mock_message = MagicMock()
        mock_message.body = b"invalid json"
        mock_message.process = mock_process
        
        with patch('rabbitmq_consumer.logger') as mock_logger:
            async with mock_message.process():
                await process_message(mock_message)
            
            mock_logger.error.assert_called()
    
    # Remove @pytest.mark.asyncio from non-async function
    def test_supported_events(self):
        """Test supported events list"""
        assert "order_placed" in SUPPORTED_EVENTS
        assert "order_failed" in SUPPORTED_EVENTS
        assert "order_completed" in SUPPORTED_EVENTS


class TestMainEndpoints:
    """Test main service endpoints"""
    
    @pytest.mark.asyncio
    async def test_root(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "notification-service"
        assert "status" in data
        assert "supported_events" in data
    
    @pytest.mark.asyncio
    async def test_health(self, client):
        """Test health endpoint"""
        with patch('main.rabbitmq_connection', None):
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "rabbitmq_connected" in data
    
    @pytest.mark.asyncio
    async def test_health_with_connection(self, client):
        """Test health endpoint with RabbitMQ connection"""
        mock_connection = MagicMock()
        mock_connection.is_closed = False
        
        with patch('main.rabbitmq_connection', mock_connection):
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["rabbitmq_connected"] is True

