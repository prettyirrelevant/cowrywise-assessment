from datetime import timedelta

import shortuuid

from django.test import TestCase
from django.utils import timezone

from librarian.apps.books.models import Book, BorrowedBook


class TestBookModel(TestCase):
    def setUp(self):
        self.user_id = f'user_{shortuuid.uuid()}'
        self.book = Book.objects.create(
            id=f'book_{shortuuid.uuid()}',
            title='To Kill a Mockingbird',
            author='Harper Lee',
            added_by=self.user_id,
            isbn='9780061120084',
            category='Fiction',
            publisher='HarperCollins',
        )

    def test_book_creation(self):
        self.assertTrue(isinstance(self.book, Book))
        self.assertEqual(self.book.category, 'Fiction')
        self.assertEqual(self.book.author, 'Harper Lee')
        self.assertTrue(self.book.id.startswith('book_'))
        self.assertEqual(self.book.isbn, '9780061120084')
        self.assertEqual(self.book.publisher, 'HarperCollins')
        self.assertTrue(self.book.added_by.startswith('user_'))
        self.assertEqual(self.book.title, 'To Kill a Mockingbird')

    def test_book_str_method(self):
        self.assertEqual(str(self.book), 'To Kill a Mockingbird')

    def test_book_is_available(self):
        self.assertTrue(self.book.is_available())

        BorrowedBook.objects.create(
            book=self.book,
            id=f'borrowed_{shortuuid.uuid()}',
            borrower=f'user_{shortuuid.uuid()}',
            proposed_return_date=timezone.now() + timedelta(days=14),
        )
        self.assertFalse(self.book.is_available())

    def test_book_current_borrowing(self):
        self.assertIsNone(self.book.current_borrowing())

        borrowed_book = BorrowedBook.objects.create(
            book=self.book,
            id=f'borrowed_{shortuuid.uuid()}',
            borrower=f'user_{shortuuid.uuid()}',
            proposed_return_date=timezone.now() + timedelta(days=14),
        )
        self.assertEqual(self.book.current_borrowing(), borrowed_book)


class TestBorrowedBookModel(TestCase):
    def setUp(self):
        self.user_id = f'user_{shortuuid.uuid()}'
        self.book = Book.objects.create(
            id=f'book_{shortuuid.uuid()}',
            title='The Midnight Library',
            added_by=self.user_id,
            author='Matt Haig',
            isbn='9781984801258',
            category='Fiction',
            publisher='Viking',
        )
        self.borrowed_book = BorrowedBook.objects.create(
            book=self.book,
            borrower=self.user_id,
            id=f'borrowed_{shortuuid.uuid()}',
            proposed_return_date=timezone.now() + timedelta(days=21),
        )

    def test_borrowed_book_creation(self):
        self.assertFalse(self.borrowed_book.is_returned)
        self.assertIsNotNone(self.borrowed_book.created_at)
        self.assertEqual(self.borrowed_book.book, self.book)
        self.assertIsNone(self.borrowed_book.actual_return_date)
        self.assertTrue(isinstance(self.borrowed_book, BorrowedBook))
        self.assertTrue(self.borrowed_book.id.startswith('borrowed_'))
        self.assertTrue(self.borrowed_book.borrower.startswith('user_'))

    def test_borrowed_book_str_method(self):
        expected_str = f'The Midnight Library - borrowed by {self.borrowed_book.borrower}'
        self.assertEqual(str(self.borrowed_book), expected_str)

    def test_return_book(self):
        self.borrowed_book.return_book()
        self.assertTrue(self.borrowed_book.is_returned)
        self.assertIsNotNone(self.borrowed_book.actual_return_date)

    def test_return_book_already_returned(self):
        self.borrowed_book.return_book()
        initial_return_date = self.borrowed_book.actual_return_date

        # try to return the book again
        self.borrowed_book.return_book()

        # check that the actual_return_date hasn't changed
        self.assertEqual(self.borrowed_book.actual_return_date, initial_return_date)

    def test_book_availability_after_return(self):
        self.assertFalse(self.book.is_available())
        self.borrowed_book.return_book()
        self.assertTrue(self.book.is_available())

    def test_overdue_borrowing(self):
        # create a borrowing that's overdue
        overdue_borrowing = BorrowedBook.objects.create(
            id=f'borrowed_{shortuuid.uuid()}',
            book=Book.objects.create(
                id=f'book_{shortuuid.uuid()}',
                title='Overdue Book',
                added_by=self.user_id,
                author='Test Author',
                isbn='1234567890123',
                category='Test',
                publisher='Test Publisher',
            ),
            borrower=f'user_{shortuuid.uuid()}',
            proposed_return_date=timezone.now() - timedelta(days=1),
        )

        # check if the borrowing is overdue
        self.assertTrue(overdue_borrowing.proposed_return_date < timezone.now())

        # the book should not be available
        self.assertFalse(overdue_borrowing.book.is_available())

        overdue_borrowing.return_book()
        self.assertTrue(overdue_borrowing.book.is_available())
