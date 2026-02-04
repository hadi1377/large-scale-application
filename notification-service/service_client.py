"""
Service client module with circuit breaker pattern for external service calls.
Uses aiobreaker to implement circuit breakers for resilient service communication.
"""
import httpx
import logging
from datetime import timedelta
from typing import Optional, Dict, Any
from aiobreaker import CircuitBreaker, CircuitBreakerError

logger = logging.getLogger(__name__)

# Service URLs
USER_SERVICE_URL = "http://user-service:8000"

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


# Create circuit breaker for user service
user_service_cb = create_circuit_breaker("user-service")


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


def get_circuit_breaker_state(service_name: str) -> Dict[str, Any]:
    """
    Get the current state of a circuit breaker for monitoring.
    
    Args:
        service_name: Name of the service (user-service)
    
    Returns:
        Dictionary with circuit breaker state information
    """
    circuit_breakers = {
        "user-service": user_service_cb
    }
    
    cb = circuit_breakers.get(service_name)
    if not cb:
        return {"error": f"Unknown service: {service_name}"}
    
    state = cb.current_state
    return {
        "service": service_name,
        "state": state.name if hasattr(state, 'name') else str(state),
        "fail_counter": cb.fail_counter,
        "success_counter": cb.success_counter,
        "last_failure": str(cb.last_failure) if cb.last_failure else None,
        "opened_at": str(cb.opened_at) if cb.opened_at else None
    }


