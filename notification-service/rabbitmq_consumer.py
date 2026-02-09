import aio_pika
import json
import logging
import os
from email_service import send_order_notification

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://rabbitmq_user:rabbitmq_password@rabbitmq:5672/")
EXCHANGE_NAME = "order_events"
QUEUE_NAME = "notification_queue"

# Events we want to listen to
SUPPORTED_EVENTS = ["order_placed", "order_failed", "order_completed"]


async def process_message(message: aio_pika.IncomingMessage):
    """Process incoming RabbitMQ message."""
    async with message.process():
        try:
            # Parse message body
            body = message.body.decode()
            data = json.loads(body)
            
            event_type = data.get("event_type")
            order_data = data.get("order_data", {})
            
            logger.info(f"Received event: {event_type} for order: {order_data.get('order_id')}")
            
            # Check if event is supported
            if event_type not in SUPPORTED_EVENTS:
                logger.warning(f"Unsupported event type: {event_type}")
                return
            
            # Send email notification
            success = await send_order_notification(event_type, order_data)
            
            if success:
                logger.info(f"Successfully sent notification for {event_type} event")
            else:
                logger.error(f"Failed to send notification for {event_type} event")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")


async def start_consumer():
    """Start RabbitMQ consumer."""
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            # Connect to RabbitMQ
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            logger.info("Connected to RabbitMQ")
            
            # Create channel
            channel = await connection.channel()
            
            # Declare exchange (topic exchange for routing)
            exchange = await channel.declare_exchange(
                EXCHANGE_NAME,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            # Declare queue
            queue = await channel.declare_queue(QUEUE_NAME, durable=True)
            
            # Bind queue to exchange for each event type
            for event_type in SUPPORTED_EVENTS:
                await queue.bind(exchange, routing_key=event_type)
                logger.info(f"Bound queue to exchange with routing key: {event_type}")
            
            # Start consuming messages
            await queue.consume(process_message)
            logger.info("Started consuming messages from RabbitMQ")
            
            # Keep connection alive
            return connection
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                import asyncio
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Could not connect to RabbitMQ.")
                raise





