import aio_pika
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

RABBIT_URI = os.getenv("RABBIT_URI", "amqp://guest:guest@rabbitmq/")
RABBIT_EXCHANGE = os.getenv("RABBIT_EXCHANGE", "user_events")
RABBIT_ROUTING_KEY = os.getenv("RABBIT_ROUTING_KEY", "user.update")
RETRY_DELAY = 2
MAX_RETRIES = 20


async def get_rabbit_connection():
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"Connecting to RabbitMQ (attempt {attempt}/{MAX_RETRIES})...")
            conn = await aio_pika.connect_robust(RABBIT_URI)
            print("Connected to RabbitMQ!")
            return conn
        except Exception as e:
            print(f"RabbitMQ not ready: {e}. Retrying in {RETRY_DELAY}s...")
            await asyncio.sleep(RETRY_DELAY)

    raise RuntimeError("Failed to connect to RabbitMQ after retrying")


async def setup_channel():
    connection = await get_rabbit_connection()
    channel = await connection.channel()

    # ensure the exchange exists
    exchange = await channel.declare_exchange(
        RABBIT_EXCHANGE,
        aio_pika.ExchangeType.TOPIC,
        durable=True
    )

    # create a fresh queue for the event system
    queue = await channel.declare_queue(
        "user_update_queue",
        durable=True
    )

    # bind queue to routing key
    await queue.bind(exchange, routing_key=RABBIT_ROUTING_KEY)

    return connection, channel, queue
