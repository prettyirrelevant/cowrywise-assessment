import logging
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand

from bookcourier import BookCourier, LibraryMessage

from bookworm.apps.books.models import Book

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process book management events from RabbitMQ queue'

    def process_event(self, event: LibraryMessage) -> None:
        try:
            event_type = event.get('event')
            if event_type == 'book_added':
                data = event.get('book')
                Book.objects.create(
                    id=data.get('id'),
                    isbn=data.get('isbn'),
                    title=data.get('title'),
                    author=data.get('author'),
                    added_by=data.get('added_by'),
                    category=data.get('category'),
                    publisher=data.get('publisher'),
                    created_at=data.get('created_at'),
                    updated_at=data.get('updated_at'),
                )
            elif event_type == 'book_removed':
                Book.objects.delete(id=event.get('book_id'))
            else:
                logger.debug('Skipping unsupported event: %s', event_type)
        except Exception:
            logger.exception('Error processing event: %s', event)

    def handle(self, *args: Any, **options: Any) -> None:
        bookcourier: BookCourier = settings.BOOKCOURIER
        logger.info('Starting to management events...')
        try:
            bookcourier.consume_events(
                queue='management',
                callback=self.process_event,
            )
        except KeyboardInterrupt:
            logger.info('Stopped processing events due to keyboard interrupt')
        except Exception:
            logger.exception('Error occurred while processing book management events')
        finally:
            logger.info('Finished processing book management events')
