import shortuuid

from django.db import models
from django.utils import timezone

from bookworm.common.models import TimestampedModel


class Book(TimestampedModel):
    id = models.CharField(max_length=27, unique=True, primary_key=True)

    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    added_by = models.CharField(max_length=27)
    category = models.CharField(max_length=100)
    publisher = models.CharField(max_length=200)
    isbn = models.CharField(max_length=13, unique=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs) -> None:
        now = timezone.now()
        if not self.created_at:
            self.created_at = now

        if not self.updated_at:
            self.updated_at = now

        if not self.id:
            self.id = f'book_{shortuuid.uuid()}'

        return super().save(*args, **kwargs)

    def is_available(self):
        return not self.borrowing_records.filter(is_returned=False).exists()

    def current_borrowing(self):
        return self.borrowing_records.filter(is_returned=False).first()


class BorrowedBook(TimestampedModel):
    id = models.CharField(max_length=31, unique=True, primary_key=True)

    proposed_return_date = models.DateTimeField()
    is_returned = models.BooleanField(default=False)
    borrower = models.CharField(max_length=27, db_index=True)
    actual_return_date = models.DateTimeField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrowing_records')

    def __str__(self):
        status = 'returned' if self.is_returned else 'borrowed'
        return f'{self.book.title} - {status} by {self.borrower}'

    def save(self, *args, **kwargs) -> None:
        now = timezone.now()
        if not self.created_at:
            self.created_at = now

        if not self.updated_at:
            self.updated_at = now

        if not self.id:
            self.id = f'borrowed_{shortuuid.uuid()}'

        return super().save(*args, **kwargs)
