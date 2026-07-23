# Email Service
import sendgrid

async def send_order_confirmation(order, recipient):
    template_id = "d-abc123"
    await sg_client.send(template_id, recipient, order)
