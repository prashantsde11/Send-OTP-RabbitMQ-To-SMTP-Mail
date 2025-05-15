import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class Settings:
    # RabbitMQ connection URL
    RABBITMQ_URL = os.getenv("RABBITMQ_URL")
    # Redis connection URL
    REDIS_URL = os.getenv("REDIS_URL")
    # SMTP email settings for sending OTP emails
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = os.getenv("SMTP_PORT")
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")

# Instantiate settings class to use throughout the app
settings = Settings()
