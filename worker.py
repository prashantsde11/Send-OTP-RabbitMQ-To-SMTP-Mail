import asyncio
import aio_pika
import json
import aioredis
import aiosmtplib
from email.message import EmailMessage
from app.config import settings
from pathlib import Path

# Function to read the HTML template for the OTP email from a file
def load_html_template(filepath: str, otp: str) -> str:
    try:
        # Open the HTML template file and read its content
        with open(filepath, 'r') as file:
            html_content = file.read()
        
        # Replace the {{ otp }} placeholder in the template with the actual OTP
        return html_content.replace("{{ otp }}", otp)
    
    except Exception as e:
        print(f"Error loading HTML template: {e}")
        return ""

# Function to send the OTP email using SMTP
async def send_email(to_email: str, otp: str):
    try:
        # Load the HTML template and replace the OTP value
        html_content = load_html_template("app/templates/otp_template.html", otp)
        
        # Create an email message object
        msg = EmailMessage()
        msg["From"] = settings.SMTP_USER  # Sender's email address
        msg["To"] = to_email  # Recipient's email address
        msg["Subject"] = "Your OTP Code"  # Email subject

        # Fallback text for email clients that don't support HTML
        msg.set_content("This is a fallback text for email clients that don't support HTML.")
        # Add the HTML version of the email
        msg.add_alternative(html_content, subtype="html")

        # Send the email using SMTP with TLS encryption
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASS,
            start_tls=True,
        )
        print(f"OTP email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")

# Function to store the OTP in Redis with a 5-minute expiration time
async def store_otp(email: str, otp: str):
    try:
        redis = await aioredis.from_url(settings.REDIS_URL)
        # Store the OTP in Redis with a key of the form otp:<email>
        await redis.set(f"otp:{email}", otp, ex=300)  # OTP expires in 5 minutes
        await redis.close()
    except Exception as e:
        print(f"Error storing OTP in Redis: {e}")

# Function to process incoming messages from RabbitMQ
async def handle_message(message: aio_pika.IncomingMessage):
    async with message.process():
        # Deserialize the message from JSON format
        data = json.loads(message.body)
        email = data["email"]
        otp = data["otp"]
        queue_name = data["queue_name"]
        print(f"Received message for queue: {queue_name}")
        
        # Store OTP in Redis and send the OTP email
        await store_otp(email, otp)
        await send_email(email, otp)

# Main worker function that listens for RabbitMQ messages
async def main():
    try:
        # Connect to RabbitMQ server
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        channel = await connection.channel()

        # Declare the exchange and queue to listen on
        exchange = await channel.declare_exchange("otp_exchange", aio_pika.ExchangeType.DIRECT, durable=True)
        queue = await channel.declare_queue("otp_queue", durable=True)
        await queue.bind(exchange)

        # Start consuming messages from the queue
        await queue.consume(handle_message)
        print(" [*] Waiting for messages...")
        await asyncio.Future()  # Keeps the worker running
    except Exception as e:
        print(f"Error in worker: {e}")

# Run the worker to start consuming messages
if __name__ == "__main__":
    asyncio.run(main())
