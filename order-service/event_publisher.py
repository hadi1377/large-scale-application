import aio_pika
import json
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://rabbitmq_user:rabbitmq_password@rabbitmq:5672/")
EXCHANGE_NAME = "order_events"

# Global connection and channel
_connection: Optional[aio_pika.Connection] = None
_channel: Optional[aio_pika.Channel] = None
_exchange: Optional[aio_pika.Exchange] = None


async def get_connection() -> aio_pika.Connection:
    """Get or create RabbitMQ connection."""
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(RABBITMQ_URL)
        logger.info("Connected to RabbitMQ")
    return _connection


async def get_exchange() -> aio_pika.Exchange:
    """Get or create RabbitMQ exchange."""
    global _channel, _exchange
    if _exchange is None or _channel.is_closed:
        connection = await get_connection()
        _channel = await connection.channel()
        _exchange = await _channel.declare_exchange(
            EXCHANGE_NAME,
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        logger.info(f"Declared exchange: {EXCHANGE_NAME}")
    return _exchange


async def publish_event(event_type: str, order_data: dict) -> bool:
    """
    Publish an order event to RabbitMQ.
    
    Args:
        event_type: Type of event (order_placed, order_failed, order_completed)
        order_data: Dictionary containing order information
    
    Returns:
        True if event was published successfully, False otherwise
    """
    try:
        exchange = await get_exchange()
        
        # Prepare message
        message_body = json.dumps({
            "event_type": event_type,
            "order_data": order_data
        })
        
        # Publish message
        await exchange.publish(
            aio_pika.Message(
                message_body.encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=event_type
        )
        
        logger.info(f"Published event: {event_type} for order: {order_data.get('order_id')}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to publish event {event_type}: {str(e)}")
        return False


async def close_connection():
    """Close RabbitMQ connection."""
    global _connection, _channel, _exchange
    if _connection and not _connection.is_closed:
        await _connection.close()
        _connection = None
        _channel = None
        _exchange = None
        logger.info("RabbitMQ connection closed")





