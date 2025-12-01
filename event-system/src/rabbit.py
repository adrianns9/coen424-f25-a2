import aio_pika
import os
from dotenv import load_dotenv

load_dotenv()

RABBIT_URI = os.getenv("RABBIT_URI", "amqp://guest:guest@rabbitmq/")
RABBIT_EXCHANGE = os.getenv("RABBIT_EXCHANGE", "user_events")
RABBIT_ROUTING_KEY = os.getenv("RABBIT_ROUTING_KEY", "user.update")


async def get_rabbit_connection():
    return await aio_pika.connect_robust(RABBIT_URI)


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
