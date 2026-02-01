import aiosmtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

logger = logging.getLogger(__name__)

# Mailpit SMTP configuration
SMTP_HOST = os.getenv("SMTP_HOST", "mailpit")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@example.com")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Order Service")

# User service URL to fetch user details
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000")


async def get_user_email(user_id: str) -> str:
    """Fetch user email from user-service."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}")
            if response.status_code == 200:
                user_data = response.json()
                return user_data.get("email", "")
            else:
                logger.error(f"Failed to fetch user {user_id}: HTTP {response.status_code}")
                return ""
    except Exception as e:
        logger.error(f"Error fetching user email for {user_id}: {str(e)}")
        return ""


def get_email_subject(event_type: str) -> str:
    """Get email subject based on event type."""
    subjects = {
        "order_placed": "Order Placed Successfully",
        "order_failed": "Order Failed",
        "order_completed": "Order Completed"
    }
    return subjects.get(event_type, "Order Update")


def get_email_body(event_type: str, order_data: dict) -> str:
    """Generate email body based on event type and order data."""
    order_id = order_data.get("order_id", "N/A")
    total_amount = order_data.get("total_amount", "N/A")
    status = order_data.get("status", "N/A")
    
    if event_type == "order_placed":
        return f"""
        <html>
        <body>
            <h2>Order Placed Successfully</h2>
            <p>Dear Customer,</p>
            <p>Your order has been placed successfully!</p>
            <p><strong>Order ID:</strong> {order_id}</p>
            <p><strong>Total Amount:</strong> ${total_amount}</p>
            <p><strong>Status:</strong> {status}</p>
            <p>We will process your order and keep you updated.</p>
            <p>Thank you for your purchase!</p>
        </body>
        </html>
        """
    elif event_type == "order_failed":
        return f"""
        <html>
        <body>
            <h2>Order Failed</h2>
            <p>Dear Customer,</p>
            <p>We regret to inform you that your order could not be processed.</p>
            <p><strong>Order ID:</strong> {order_id}</p>
            <p><strong>Total Amount:</strong> ${total_amount}</p>
            <p><strong>Status:</strong> {status}</p>
            <p>Please contact our support team if you have any questions.</p>
            <p>We apologize for any inconvenience.</p>
        </body>
        </html>
        """
    elif event_type == "order_completed":
        return f"""
        <html>
        <body>
            <h2>Order Completed</h2>
            <p>Dear Customer,</p>
            <p>Great news! Your order has been completed.</p>
            <p><strong>Order ID:</strong> {order_id}</p>
            <p><strong>Total Amount:</strong> ${total_amount}</p>
            <p><strong>Status:</strong> {status}</p>
            <p>Thank you for shopping with us!</p>
        </body>
        </html>
        """
    else:
        return f"""
        <html>
        <body>
            <h2>Order Update</h2>
            <p>Dear Customer,</p>
            <p>Your order status has been updated.</p>
            <p><strong>Order ID:</strong> {order_id}</p>
            <p><strong>Total Amount:</strong> ${total_amount}</p>
            <p><strong>Status:</strong> {status}</p>
        </body>
        </html>
        """


async def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send email using Mailpit SMTP server."""
    if not to_email:
        logger.error("No recipient email provided")
        return False
    
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        message["To"] = to_email
        message["Subject"] = subject
        
        # Add HTML body
        html_part = MIMEText(body, "html")
        message.attach(html_part)
        
        # Send email
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER if SMTP_USER else None,
            password=SMTP_PASSWORD if SMTP_PASSWORD else None,
            use_tls=False  # Mailpit doesn't require TLS
        )
        
        logger.info(f"Email sent successfully to {to_email} with subject: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


async def send_order_notification(event_type: str, order_data: dict) -> bool:
    """Send order notification email to user."""
    user_id = order_data.get("user_id")
    if not user_id:
        logger.error("No user_id in order data")
        return False
    
    # Get user email
    user_email = await get_user_email(str(user_id))
    if not user_email:
        logger.error(f"Could not fetch email for user {user_id}")
        return False
    
    # Generate email content
    subject = get_email_subject(event_type)
    body = get_email_body(event_type, order_data)
    
    # Send email
    return await send_email(user_email, subject, body)

