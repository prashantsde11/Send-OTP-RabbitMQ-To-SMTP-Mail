from fastapi import FastAPI, HTTPException
import aio_pika
import json
from pydantic import BaseModel
from app.config import settings

app = FastAPI()

# Pydantic model for validating the OTP request
class OTPRequest(BaseModel):
    email: str  # Email address to send the OTP
    otp: str    # The OTP value to send

    # Example request for API documentation
    class Config:
        schema_extra = {
            "example": {
                "email": "user@gmail.com",
                "otp": "123456"
            }
        }

# Function to send the OTP message to RabbitMQ
async def publish_otp_message(message: dict):
    try:
        # Connect to RabbitMQ server
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()

            # Declare the exchange and queue
            exchange = await channel.declare_exchange("otp_exchange", aio_pika.ExchangeType.DIRECT, durable=True)
            queue = await channel.declare_queue("otp_queue", durable=True)
            await queue.bind(exchange)

            # Publish the OTP message to the RabbitMQ queue
            await exchange.publish(
                aio_pika.Message(body=json.dumps(message).encode()),
                routing_key="otp_queue"
            )
            print(f"Message sent to queue otp_queue")
    except Exception as e:
        print(f"Error publishing message: {e}")

# FastAPI endpoint for sending OTP
@app.post("/send-otp")
async def send_otp(request: OTPRequest):
    try:
        # Prepare the message to be sent to RabbitMQ
        message = {
            "email": request.email,
            "otp": request.otp,
            "queue_name": "otp_queue"
        }

        # Call the function to publish the OTP message
        await publish_otp_message(message)
        return {"message": "OTP sent to queue successfully"}
    except Exception as e:
        # If there's an error, raise an HTTP exception
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
