from fastapi import FastAPI
import asyncio
import logging
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
from rabbitmq_consumer import start_consumer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variable to store RabbitMQ connection
rabbitmq_connection = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start RabbitMQ consumer
    global rabbitmq_connection
    try:
        logger.info("Starting notification service...")
        rabbitmq_connection = await start_consumer()
        logger.info("Notification service started successfully")
    except Exception as e:
        logger.error(f"Failed to start notification service: {str(e)}")
        # Don't raise - let the service start even if RabbitMQ is unavailable
        # It will retry in the background
    
    yield
    
    # Shutdown: Close RabbitMQ connection
    if rabbitmq_connection:
        try:
            await rabbitmq_connection.close()
            logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {str(e)}")


app = FastAPI(
    title="Notification Service",
    description="Notification service for sending emails on order events",
    version="1.0.0",
    lifespan=lifespan
)

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)


@app.get("/")
def root():
    return {
        "service": "notification-service",
        "status": "running",
        "supported_events": ["order_placed", "order_failed", "order_completed"]
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "rabbitmq_connected": rabbitmq_connection is not None and not rabbitmq_connection.is_closed
    }

