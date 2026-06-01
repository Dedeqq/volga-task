"""RabbitMQ message queue client."""

import json
import aio_pika
from typing import Dict, Any, Optional
from app.config import settings


class RabbitMQClient:
    """Handle RabbitMQ message operations."""

    def __init__(self):
        """Initialize RabbitMQ client."""
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None

    async def connect(self):
        """Connect to RabbitMQ server."""
        try:
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            self.channel = await self.connection.channel()

            # Declare queue with durability
            self.queue = await self.channel.declare_queue(
                settings.TRANSCRIPTION_QUEUE,
                durable=True,
            )

            print(f"Connected to RabbitMQ on {settings.RABBITMQ_URL}")
            return True
        except Exception as e:
            print(f"Error connecting to RabbitMQ: {e}")
            return False

    async def disconnect(self):
        """Disconnect from RabbitMQ."""
        try:
            if self.connection:
                await self.connection.close()
                print("Disconnected from RabbitMQ")
        except Exception as e:
            print(f"Error disconnecting from RabbitMQ: {e}")

    async def publish_job(self, job_data: Dict[str, Any]) -> bool:
        """
        Publish a job to the queue.

        Args:
            job_data: Job data dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.channel or not self.queue:
                await self.connect()

            message = aio_pika.Message(
                body=json.dumps(job_data).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )

            await self.channel.default_exchange.publish(
                message,
                routing_key=settings.TRANSCRIPTION_QUEUE,
            )

            print(f"Published job {job_data.get('job_id')} to queue")
            return True
        except Exception as e:
            print(f"Error publishing job to queue: {e}")
            return False

    async def consume_jobs(self, callback):
        """
        Consume jobs from the queue.

        Args:
            callback: Async function to handle each job
        """
        try:
            if not self.channel or not self.queue:
                await self.connect()

            async with self.queue.iterator() as queue_iter:
                async for message in queue_iter:
                    try:
                        job_data = json.loads(message.body.decode())
                        await callback(job_data)
                        await message.ack()
                    except Exception as e:
                        print(f"Error processing job: {e}")
                        await message.nack(requeue=True)
        except Exception as e:
            print(f"Error consuming jobs: {e}")
