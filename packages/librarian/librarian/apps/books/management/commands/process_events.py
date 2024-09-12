import logging
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand

from bookcourier import BookCourier, LibraryMessage

from librarian.apps.books.models import BorrowedBook

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process book transactions events from RabbitMQ queue'

    def process_event(self, event: LibraryMessage) -> None:
        try:
            event_type = event.get('event')
            if event_type == 'book_borrowed':
                data = event.get('borrowed_book')
                user_id = data.get('user_id')
                book_id = data.get('book_id')

                logger.info('Processing borrowed book with id %s by %s...', book_id, user_id)
                BorrowedBook.objects.create(
                    book_id=book_id,
                    borrower=user_id,
                    id=data.get('id'),
                    created_at=data.get('created_at'),
                    updated_at=data.get('updated_at'),
                    proposed_return_date=data.get('proposed_return_date'),
                )
            elif event_type == 'book_returned':
                borrowed_book_id = event.get('borrowed_book_id')
                actual_return_date = event.get('actual_return_date')

                logger.info('Processing returned book with id %s...', borrowed_book_id)
                BorrowedBook.objects.filter(id=borrowed_book_id).update(
                    is_returned=True,
                    updated_at=actual_return_date,
                    actual_return_date=actual_return_date,
                )
            else:
                logger.debug('Skipping unsupported event: %s', event_type)
        except Exception:
            logger.exception('Error processing event: %s', event)

    def handle(self, *args: Any, **options: Any) -> None:
        bookcourier: BookCourier = settings.BOOKCOURIER
        logger.info('Starting to process book transaction events...')
        try:
            bookcourier.consume_events(
                queue='transaction',
                callback=self.process_event,
            )
        except KeyboardInterrupt:
            logger.info('Stopped processing events due to keyboard interrupt')
        except Exception:
            logger.exception('Error occurred while processing book transaction events')
        finally:
            logger.info('Finished processing booktransaction events')
