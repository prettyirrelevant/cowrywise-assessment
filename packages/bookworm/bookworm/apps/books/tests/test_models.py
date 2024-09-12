import datetime

from django.test import TestCase
from django.utils import timezone

from bookworm.apps.books.models import Book, BorrowedBook


class BookModelTest(TestCase):
    def setUp(self):
        self.book = Book.objects.create(
            title='To Kill a Mockingbird',
            author='Harper Lee',
            added_by='user_123456789',
            category='Fiction',
            publisher='J. B. Lippincott & Co.',
            isbn='9780446310789',
        )

    def test_book_creation(self):
        self.assertTrue(isinstance(self.book, Book))
        self.assertEqual(self.book.__str__(), 'To Kill a Mockingbird')

    def test_book_id_generation(self):
        self.assertTrue(self.book.id.startswith('book_'))
        self.assertEqual(len(self.book.id), 27)  # 'book_' + 22 characters

    def test_is_available_method(self):
        self.assertTrue(self.book.is_available())

        # Create a borrowed book record
        BorrowedBook.objects.create(
            book=self.book,
            borrower='borrower_123',
            proposed_return_date=timezone.now() + datetime.timedelta(days=14),
        )

        self.assertFalse(self.book.is_available())

    def test_current_borrowing_method(self):
        self.assertIsNone(self.book.current_borrowing())

        borrowed_book = BorrowedBook.objects.create(
            book=self.book,
            borrower='borrower_123',
            proposed_return_date=timezone.now() + datetime.timedelta(days=14),
        )

        self.assertEqual(self.book.current_borrowing(), borrowed_book)

    def test_multiple_borrowings(self):
        # Create two borrowings, one returned and one active
        BorrowedBook.objects.create(
            book=self.book,
            is_returned=True,
            borrower='borrower_123',
            actual_return_date=timezone.now() - datetime.timedelta(days=5),
            proposed_return_date=timezone.now() - datetime.timedelta(days=7),
        )
        active_borrowing = BorrowedBook.objects.create(
            book=self.book,
            borrower='borrower_456',
            proposed_return_date=timezone.now() + datetime.timedelta(days=7),
        )

        self.assertFalse(self.book.is_available())
        self.assertEqual(self.book.current_borrowing(), active_borrowing)


class BorrowedBookModelTest(TestCase):
    def setUp(self):
        self.book = Book.objects.create(
            title='1984',
            author='George Orwell',
            added_by='user_987654321',
            category='Science Fiction',
            publisher='Secker & Warburg',
            isbn='9780451524935',
        )
        self.borrowed_book = BorrowedBook.objects.create(
            book=self.book,
            borrower='user_wofnwrf434343',
            proposed_return_date=timezone.now() + datetime.timedelta(days=14),
        )

    def test_borrowed_book_creation(self):
        self.assertTrue(isinstance(self.borrowed_book, BorrowedBook))
        self.assertEqual(str(self.borrowed_book), '1984 - borrowed by user_wofnwrf434343')

    def test_borrowed_book_id_generation(self):
        self.assertTrue(self.borrowed_book.id.startswith('borrowed_'))
        self.assertEqual(len(self.borrowed_book.id), 31)  # 'borrowed_' + 26 characters

    def test_return_book(self):
        self.assertFalse(self.borrowed_book.is_returned)
        self.assertIsNone(self.borrowed_book.actual_return_date)

        # Simulate returning the book
        self.borrowed_book.is_returned = True
        self.borrowed_book.actual_return_date = timezone.now()
        self.borrowed_book.save()

        # Refresh from database
        self.borrowed_book.refresh_from_db()

        self.assertTrue(self.borrowed_book.is_returned)
        self.assertIsNotNone(self.borrowed_book.actual_return_date)
        self.assertEqual(str(self.borrowed_book), '1984 - returned by user_wofnwrf434343')

    def test_overdue_book(self):
        # Create an overdue borrowed book
        overdue_book = BorrowedBook.objects.create(
            book=self.book,
            borrower='borrower_101',
            proposed_return_date=timezone.now() - datetime.timedelta(days=1),
        )

        self.assertFalse(overdue_book.is_returned)
        self.assertTrue(overdue_book.proposed_return_date < timezone.now())

    def test_multiple_borrowings_for_book(self):
        # Create another borrowing for the same book
        another_borrowing = BorrowedBook.objects.create(
            book=self.book,
            borrower='borrower_202',
            proposed_return_date=timezone.now() + datetime.timedelta(days=7),
        )

        book_borrowings = self.book.borrowing_records.all()
        self.assertEqual(book_borrowings.count(), 2)
        self.assertIn(self.borrowed_book, book_borrowings)
        self.assertIn(another_borrowing, book_borrowings)
