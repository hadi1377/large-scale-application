"""
Service client module with circuit breaker pattern for external service calls.
Uses aiobreaker to implement circuit breakers for resilient service communication.
"""
import httpx
import logging
import os
from datetime import timedelta
from typing import Optional, Dict, Any
from aiobreaker import CircuitBreaker, CircuitBreakerError

logger = logging.getLogger(__name__)

# Service URLs
PRODUCT_SERVICE_URL = "http://product-service:8000"
USER_SERVICE_URL = "http://user-service:8000"
PAYMENT_SERVICE_URL = "http://payment-service:8000"

# API Key for payment service authentication
PAYMENT_SERVICE_API_KEY = os.getenv("PAYMENT_SERVICE_API_KEY", "change-me-in-production")

# Circuit breaker configuration
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5  # Open circuit after 5 failures
CIRCUIT_BREAKER_TIMEOUT = timedelta(seconds=60)  # Timeout before attempting to close circuit


def create_circuit_breaker(name: str) -> CircuitBreaker:
    """
    Create a circuit breaker instance with configured settings.
    
    Args:
        name: Name of the circuit breaker (for logging)
    
    Returns:
        CircuitBreaker instance
    """
    return CircuitBreaker(
        fail_max=CIRCUIT_BREAKER_FAILURE_THRESHOLD,
        timeout_duration=CIRCUIT_BREAKER_TIMEOUT
    )


# Create circuit breakers for each service
product_service_cb = create_circuit_breaker("product-service")
user_service_cb = create_circuit_breaker("user-service")
payment_service_cb = create_circuit_breaker("payment-service")


@user_service_cb
async def _call_user_service_internal(
    url: str,
    method: str,
    headers: Optional[Dict[str, str]],
    json_data: Optional[Dict[str, Any]],
    timeout: float
) -> httpx.Response:
    """Internal function to make HTTP request to user service."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        if method.upper() == "GET":
            return await client.get(url, headers=headers)
        elif method.upper() == "POST":
            return await client.post(url, headers=headers, json=json_data)
        elif method.upper() == "PUT":
            return await client.put(url, headers=headers, json=json_data)
        elif method.upper() == "DELETE":
            return await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")


async def call_user_service(
    method: str,
    endpoint: str,
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0
) -> httpx.Response:
    """
    Call user service with circuit breaker protection.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        headers: Optional HTTP headers
        json_data: Optional JSON data for POST/PUT requests
        timeout: Request timeout in seconds
    
    Returns:
        httpx.Response object
    
    Raises:
        CircuitBreakerError: When circuit breaker is open
        httpx.HTTPError: For HTTP-related errors
    """
    url = f"{USER_SERVICE_URL}{endpoint}"
    
    try:
        return await _call_user_service_internal(url, method, headers, json_data, timeout)
    except CircuitBreakerError as e:
        logger.error(f"Circuit breaker is open for user-service: {e}")
        raise httpx.HTTPError(
            f"User service circuit breaker is open. Service may be unavailable."
        ) from e


@product_service_cb
async def _call_product_service_internal(
    url: str,
    method: str,
    headers: Optional[Dict[str, str]],
    json_data: Optional[Dict[str, Any]],
    timeout: float
) -> httpx.Response:
    """Internal function to make HTTP request to product service."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        if method.upper() == "GET":
            return await client.get(url, headers=headers)
        elif method.upper() == "POST":
            return await client.post(url, headers=headers, json=json_data)
        elif method.upper() == "PUT":
            return await client.put(url, headers=headers, json=json_data)
        elif method.upper() == "DELETE":
            return await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")


async def call_product_service(
    method: str,
    endpoint: str,
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0
) -> httpx.Response:
    """
    Call product service with circuit breaker protection.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        headers: Optional HTTP headers
        json_data: Optional JSON data for POST/PUT requests
        timeout: Request timeout in seconds
    
    Returns:
        httpx.Response object
    
    Raises:
        CircuitBreakerError: When circuit breaker is open
        httpx.HTTPError: For HTTP-related errors
    """
    url = f"{PRODUCT_SERVICE_URL}{endpoint}"
    
    try:
        return await _call_product_service_internal(url, method, headers, json_data, timeout)
    except CircuitBreakerError as e:
        logger.error(f"Circuit breaker is open for product-service: {e}")
        raise httpx.HTTPError(
            f"Product service circuit breaker is open. Service may be unavailable."
        ) from e


@payment_service_cb
async def _call_payment_service_internal(
    url: str,
    method: str,
    headers: Optional[Dict[str, str]],
    json_data: Optional[Dict[str, Any]],
    timeout: float
) -> httpx.Response:
    """Internal function to make HTTP request to payment service."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        if method.upper() == "GET":
            return await client.get(url, headers=headers)
        elif method.upper() == "POST":
            return await client.post(url, headers=headers, json=json_data)
        elif method.upper() == "PUT":
            return await client.put(url, headers=headers, json=json_data)
        elif method.upper() == "DELETE":
            return await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")


async def call_payment_service(
    method: str,
    endpoint: str,
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0
) -> httpx.Response:
    """
    Call payment service with circuit breaker protection.
    Automatically includes the service API key for authentication.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        headers: Optional HTTP headers (API key will be added automatically)
        json_data: Optional JSON data for POST/PUT requests
        timeout: Request timeout in seconds
    
    Returns:
        httpx.Response object
    
    Raises:
        CircuitBreakerError: When circuit breaker is open
        httpx.HTTPError: For HTTP-related errors
    """
    url = f"{PAYMENT_SERVICE_URL}{endpoint}"
    
    # Ensure headers dict exists and add API key
    if headers is None:
        headers = {}
    headers["X-Service-API-Key"] = PAYMENT_SERVICE_API_KEY
    
    try:
        return await _call_payment_service_internal(url, method, headers, json_data, timeout)
    except CircuitBreakerError as e:
        logger.error(f"Circuit breaker is open for payment-service: {e}")
        raise httpx.HTTPError(
            f"Payment service circuit breaker is open. Service may be unavailable."
        ) from e


def get_circuit_breaker_state(service_name: str) -> Dict[str, Any]:
    """
    Get the current state of a circuit breaker for monitoring.
    
    Args:
        service_name: Name of the service (user-service, product-service, payment-service)
    
    Returns:
        Dictionary with circuit breaker state information
    """
    circuit_breakers = {
        "user-service": user_service_cb,
        "product-service": product_service_cb,
        "payment-service": payment_service_cb
    }
    
    cb = circuit_breakers.get(service_name)
    if not cb:
        return {"error": f"Unknown service: {service_name}"}
    
    state = cb.current_state
    result = {
        "service": service_name,
        "state": state.name if hasattr(state, 'name') else str(state),
        "fail_counter": cb.fail_counter
    }
    # Only include attributes if they exist
    if hasattr(cb, 'success_counter'):
        result["success_counter"] = cb.success_counter
    if hasattr(cb, 'last_failure'):
        result["last_failure"] = str(cb.last_failure) if cb.last_failure else None
    if hasattr(cb, 'opened_at'):
        result["opened_at"] = str(cb.opened_at) if cb.opened_at else None
    return result

