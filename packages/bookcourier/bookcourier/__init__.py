import json
import logging
from typing import Literal
from collections.abc import Callable

import pika
import pika.exceptions
from pika.exceptions import AMQPError, AMQPConnectionError

from .types import (
    BookData,
    AddBookMessage,
    LibraryMessage,
    BorrowedBookData,
    BorrowBookMessage,
    RemoveBookMessage,
    ReturnBookMessage,
)

logger = logging.getLogger(__name__)

QueueName = Literal['management', 'transaction']


class BookCourier:
    """A service for publishing and consuming book-related events via RabbitMQ."""

    def __init__(self, rabbitmq_url: str) -> None:
        self.rabbitmq_url = rabbitmq_url
        self.queues: dict[QueueName, str] = {
            'management': 'bookcourier_management_events',
            'transaction': 'bookcourier_transaction_events',
        }
        self.channel: pika.channel.Channel | None = None
        self.connection: pika.BlockingConnection | None = None

    def _ensure_connection(self) -> None:
        """Ensure a connection to RabbitMQ is established."""
        if self.connection and self.connection.is_open:
            return

        try:
            parameters = pika.URLParameters(self.rabbitmq_url)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            for queue_name in self.queues.values():
                self.channel.queue_declare(queue=queue_name, durable=True)

            logger.info('Connected to RabbitMQ at %s', self.rabbitmq_url)
        except AMQPConnectionError:
            logger.exception('Failed to connect to RabbitMQ')

    def close(self) -> None:
        """Close the RabbitMQ connection if it's open."""
        if self.connection and self.connection.is_open:
            self.connection.close()
            logger.info('RabbitMQ connection closed')

    def publish_book_added(self, book_data: BookData) -> None:
        """Publish an event when a new book is added to the catalogue."""
        message: AddBookMessage = {'event': 'book_added', 'book': book_data}
        self._publish_event(message, 'management')

    def publish_book_removed(self, book_id: str) -> None:
        """Publish an event when a book is removed from the catalogue."""
        message: RemoveBookMessage = {'event': 'book_removed', 'book_id': book_id}
        self._publish_event(message, 'management')

    def publish_book_borrowed(self, borrowed_book_data: BorrowedBookData) -> None:
        """Publish an event when a book is borrowed."""
        message: BorrowBookMessage = {'event': 'book_borrowed', 'borrowed_book': borrowed_book_data}
        self._publish_event(message, 'transaction')

    def publish_book_returned(self, *, borrowed_book_id: str, actual_return_date: str) -> None:
        """Publish an event when a book is returned."""
        message: ReturnBookMessage = {
            'event': 'book_returned',
            'borrowed_book_id': borrowed_book_id,
            'actual_return_date': actual_return_date,
        }
        self._publish_event(message, 'transaction')

    def _publish_event(self, event: LibraryMessage, queue: QueueName) -> None:
        """Publish an event to the specified RabbitMQ queue."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self._ensure_connection()
                if not self.channel or not self.channel.is_open:
                    raise AMQPError('Channel is not open')  # noqa: TRY301, TRY003, EM101

                self.channel.basic_publish(
                    exchange='',
                    routing_key=self.queues[queue],
                    body=json.dumps(event),
                    properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE),
                )
                logger.info('Published event to %s: %s', self.queues[queue], event)
                return  # noqa: TRY300
            except (AMQPError, pika.exceptions.StreamLostError):
                logger.warning('Failed to publish event. Attempt %d of %d', attempt + 1, max_retries)
                if attempt < max_retries - 1:
                    self._reset_connection()
                else:
                    logger.exception('Failed to publish event after %d attempts', max_retries)
                    raise

    def _reset_connection(self) -> None:
        """Reset the connection and channel."""
        if self.connection:
            try:
                if self.connection.is_open:
                    self.connection.close()
            except Exception:
                logger.exception('Error while closing connection')
        self.connection = None
        self.channel = None

    def consume_events(self, *, queue: QueueName, callback: Callable[[LibraryMessage], None]) -> None:
        """Consume events from the specified RabbitMQ queue."""
        self._ensure_connection()

        def event_handler(
            ch: pika.channel.Channel,
            method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties,  # noqa: ARG001
            body: bytes,
        ) -> None:
            try:
                event: LibraryMessage = json.loads(body)
                callback(event)
            except json.JSONDecodeError:
                logger.exception('Failed to decode event')
            finally:
                ch.basic_ack(delivery_tag=method.delivery_tag)

        queue_name = self.queues[queue]
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=queue_name, on_message_callback=event_handler)

        logger.info('Waiting for events on %s. To exit press CTRL+C', queue_name)
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            logger.info('Stopped consuming events from %s', queue_name)
