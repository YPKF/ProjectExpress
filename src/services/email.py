"""
Order Confirmation Email Service

Sends HTML and plain-text order confirmation emails with retry logic
and delivery status tracking.
"""

import os
import logging
from typing import Optional
from datetime import datetime, timezone

import httpx
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from ..models.order import Order, OrderItem
from ..models.user import User

logger = logging.getLogger(__name__)

# Configuration
SMTP_API_URL = os.getenv("SMTP_API_URL", "https://api.mailprovider.com/v1/send")
SMTP_API_KEY = os.getenv("SMTP_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "orders@projectexpress.com")
FROM_NAME = os.getenv("FROM_NAME", "ProjectExpress")
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = [2, 10, 30]  # Exponential backoff

# Template setup
template_env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "..", "templates", "email")),
    autoescape=select_autoescape(["html"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


class EmailService:
    """Service for sending transactional emails."""

    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=SMTP_API_URL,
            headers={
                "Authorization": f"Bearer {SMTP_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def send_order_confirmation(self, order_id: int, db: Session) -> bool:
        """
        Send order confirmation email to the customer.

        Args:
            order_id: The order ID to send confirmation for
            db: Database session

        Returns:
            True if email was sent successfully, False otherwise
        """
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            logger.error(f"Order {order_id} not found, cannot send confirmation")
            return False

        user = db.query(User).filter(User.id == order.user_id).first()
        if not user:
            logger.error(f"User for order {order_id} not found")
            return False

        # Load order items with product details
        items = (
            db.query(OrderItem)
            .filter(OrderItem.order_id == order_id)
            .all()
        )

        # Render templates
        template_data = {
            "order": order,
            "user": user,
            "items": items,
            "order_number": order.order_number,
            "order_date": order.created_at.strftime("%B %d, %Y"),
            "estimated_delivery": self._calculate_delivery_date(order),
            "shipping_address": order.shipping_address,
            "tracking_url": f"https://projectexpress.com/orders/{order.order_number}/tracking",
            "support_email": "support@projectexpress.com",
            "store_url": "https://projectexpress.com",
        }

        html_content = self._render_template("order_confirmation.html", template_data)
        plain_content = self._render_template("order_confirmation.txt", template_data)

        if not html_content or not plain_content:
            logger.error(f"Failed to render email templates for order {order_id}")
            return False

        # Send with retry logic
        for attempt in range(MAX_RETRIES):
            try:
                payload = {
                    "from": {
                        "email": FROM_EMAIL,
                        "name": FROM_NAME,
                    },
                    "to": [
                        {
                            "email": user.email,
                            "name": user.full_name,
                        }
                    ],
                    "subject": f"Order Confirmation #{order.order_number}",
                    "html": html_content,
                    "text": plain_content,
                    "tags": ["order-confirmation", f"order-{order.order_number}"],
                    "metadata": {
                        "order_id": str(order.id),
                        "order_number": order.order_number,
                    },
                }

                response = await self.client.post("/send", json=payload)
                response.raise_for_status()

                result = response.json()
                logger.info(
                    f"Order confirmation sent for order {order.order_number} "
                    f"(message_id={result.get('message_id')})"
                )

                # Update order with email sent timestamp
                order.email_sent_at = datetime.now(timezone.utc)
                db.commit()

                return True

            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"Email send attempt {attempt + 1}/{MAX_RETRIES} failed "
                    f"for order {order.order_number}: {e.response.status_code}"
                )
                if attempt < MAX_RETRIES - 1:
                    import asyncio
                    await asyncio.sleep(RETRY_DELAY_SECONDS[attempt])

            except httpx.RequestError as e:
                logger.warning(
                    f"Email send attempt {attempt + 1}/{MAX_RETRIES} failed "
                    f"for order {order.order_number}: network error - {e}"
                )
                if attempt < MAX_RETRIES - 1:
                    import asyncio
                    await asyncio.sleep(RETRY_DELAY_SECONDS[attempt])

        logger.error(
            f"Failed to send order confirmation for {order.order_number} "
            f"after {MAX_RETRIES} attempts"
        )
        return False

    def _render_template(self, template_name: str, data: dict) -> Optional[str]:
        """Render an email template with the given data."""
        try:
            template = template_env.get_template(template_name)
            return template.render(**data)
        except Exception as e:
            logger.error(f"Template rendering failed for {template_name}: {e}")
            return None

    def _calculate_delivery_date(self, order: Order) -> str:
        """Calculate estimated delivery date based on shipping method."""
        from datetime import timedelta

        shipping_days = {
            "standard": 7,
            "express": 3,
            "overnight": 1,
        }

        days = shipping_days.get(order.shipping_method, 7)
        delivery_date = order.created_at + timedelta(days=days)

        # Skip weekends
        while delivery_date.weekday() >= 5:
            delivery_date += timedelta(days=1)

        return delivery_date.strftime("%B %d, %Y")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Module-level singleton
email_service = EmailService()
