# Unit Testing Documentation

This document describes the unit tests created for all microservices in the project.

## Overview

Comprehensive unit tests have been added to all services to cover:
- All API endpoints
- Success and failure cases
- Edge cases and error handling
- Authentication and authorization
- Input validation
- Service interactions (mocked)

## Test Structure

Each service has a `test_main.py` file containing:
- Test fixtures for common test data
- Test classes organized by functionality
- Mocked external dependencies
- Async test support where needed

## Services Tested

### 1. User Service (`user-service/test_main.py`)
**Test Coverage:**
- User registration (success, duplicate email, invalid input)
- User login (success, invalid credentials)
- Get current user (`/me` endpoint)
- Get user by ID
- Authentication token validation
- Password hashing and verification

**Test Classes:**
- `TestUserRegistration` - Registration endpoint tests
- `TestUserLogin` - Login endpoint tests
- `TestGetMe` - Current user endpoint tests
- `TestGetUserById` - User lookup tests
- `TestRootEndpoint` - Root endpoint tests
- `TestAuthFunctions` - Authentication utility tests

### 2. Product Service (`product-service/test_main.py`)
**Test Coverage:**
- Create product (success, validation errors)
- List products (pagination, filtering by category/price)
- Get product by ID
- Update product (full and partial updates)
- Delete product
- Database connection error handling

**Test Classes:**
- `TestCreateProduct` - Product creation tests
- `TestGetProducts` - Product listing tests
- `TestGetProduct` - Single product retrieval tests
- `TestUpdateProduct` - Product update tests
- `TestDeleteProduct` - Product deletion tests
- `TestRootEndpoint` - Root endpoint tests
- `TestProductToDict` - Helper function tests

### 3. Order Service (`order-service/test_main.py`)
**Test Coverage:**
- Create order (with product validation, payment processing)
- List orders (user and admin views, pagination)
- Get order by ID (with authorization checks)
- Update order status (admin only)
- Product stock validation
- Payment failure handling
- Circuit breaker health checks

**Test Classes:**
- `TestCreateOrder` - Order creation tests
- `TestListOrders` - Order listing tests
- `TestGetOrder` - Single order retrieval tests
- `TestUpdateOrder` - Order update tests
- `TestRootEndpoint` - Root endpoint tests
- `TestCircuitBreakerHealth` - Circuit breaker monitoring tests

### 4. Payment Service (`payment-service/test_main.py`)
**Test Coverage:**
- Payment success endpoint
- Payment failed endpoint
- Get order payments
- API key authentication
- Payment record creation and updates

**Test Classes:**
- `TestPaymentSuccess` - Successful payment processing
- `TestPaymentFailed` - Failed payment processing
- `TestGetOrderPayments` - Payment history retrieval
- `TestRootEndpoint` - Root endpoint tests

### 5. Notification Service (`notification-service/test_main.py`)
**Test Coverage:**
- Email service functions
- User email retrieval
- Email content generation
- Email sending (success and failure)
- RabbitMQ message processing
- Order notification sending

**Test Classes:**
- `TestEmailService` - Email service function tests
- `TestRabbitMQConsumer` - Message consumer tests
- `TestMainEndpoints` - Service endpoint tests

### 6. API Gateway (`api-gateway/test_main.py`)
**Test Coverage:**
- Root endpoint (HTML documentation)
- Health check endpoints
- Service health monitoring
- OpenAPI JSON retrieval
- Service documentation pages
- Request proxying (GET, POST, PUT, DELETE)
- Error handling (timeouts, connection errors)

**Test Classes:**
- `TestRootEndpoint` - Root endpoint tests
- `TestHealthEndpoints` - Health check tests
- `TestOpenAPIEndpoints` - OpenAPI documentation tests
- `TestProxyEndpoints` - Request proxying tests
- `TestServiceConstants` - Service configuration tests

## Running Tests

### Prerequisites
Install test dependencies for each service:
```bash
pip install pytest pytest-asyncio httpx aiosqlite
```

### Run Tests for a Single Service
```bash
cd <service-directory>
pytest test_main.py -v
```

### Run All Tests
Use the provided test runner script:
```bash
python run_tests.py
```

Or run manually for each service:
```bash
# User Service
cd user-service && pytest test_main.py -v

# Product Service
cd product-service && pytest test_main.py -v

# Payment Service
cd payment-service && pytest test_main.py -v

# Order Service
cd order-service && pytest test_main.py -v

# Notification Service
cd notification-service && pytest test_main.py -v

# API Gateway
cd api-gateway && pytest test_main.py -v
```

## Test Dependencies

All services have been updated with test dependencies in their `requirements.txt`:
- `pytest==7.4.3` - Testing framework
- `pytest-asyncio==0.21.1` - Async test support
- `httpx==0.25.2` - HTTP client for testing
- `aiosqlite==0.19.0` - SQLite async driver (for services using SQL databases)

## Mocking Strategy

Tests use mocking to isolate units:
- **External Services**: HTTP calls to other services are mocked
- **Databases**: In-memory SQLite for SQL databases, mocked collections for MongoDB
- **Message Queues**: RabbitMQ operations are mocked
- **Email Services**: SMTP operations are mocked
- **Authentication**: JWT tokens are generated for testing

## Test Coverage

Each service has comprehensive test coverage including:
- ✅ Happy path scenarios
- ✅ Error cases (404, 400, 401, 403, 500)
- ✅ Input validation
- ✅ Authentication and authorization
- ✅ Edge cases
- ✅ Service integration (mocked)

## Notes

1. **Async Tests**: Some tests use `@pytest.mark.asyncio` for async database operations, while `TestClient` from FastAPI is synchronous.

2. **Database Setup**: Tests use in-memory SQLite databases that are created and destroyed for each test session.

3. **Mocking**: External service calls are mocked to ensure tests run independently without requiring all services to be running.

4. **Authentication**: Test tokens are generated using the same JWT secret as the services for realistic testing.

## Future Improvements

- Add integration tests that test services together
- Add performance/load tests
- Add test coverage reporting
- Add CI/CD pipeline integration
- Add contract testing between services


