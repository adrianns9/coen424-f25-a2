import json
import os
import aio_pika
from dotenv import load_dotenv

load_dotenv()

RABBIT_URI = os.getenv("RABBIT_URI", "amqp://guest:guest@rabbitmq/")
RABBIT_EXCHANGE = os.getenv("RABBIT_EXCHANGE", "user_events")
RABBIT_ROUTING_KEY = os.getenv("RABBIT_ROUTING_KEY", "user.update")


async def get_connection():
    return await aio_pika.connect_robust(RABBIT_URI)


async def publish_message(message: dict, headers: dict = None):
    connection = await get_connection()
    async with connection:
        channel = await connection.channel()

        # declare same exchange as consumer
        exchange = await channel.declare_exchange(
            RABBIT_EXCHANGE,
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )

        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                headers=headers or {},
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=RABBIT_ROUTING_KEY
        )
