from datetime import timedelta
from unittest.mock import Mock

from django.test import TestCase
from django.utils import timezone

from bookworm.apps.books.models import Book, BorrowedBook
from bookworm.apps.books.serializers import (
    BookSerializer,
    UserSerializer,
    BorrowBookSerializer,
    BorrowedBookSerializer,
)


class BookSerializerTestCase(TestCase):
    def setUp(self):
        self.book_data = {
            'isbn': '9780451524935',
            'title': '1984',
            'author': 'George Orwell',
            'category': 'Fiction',
            'publisher': 'Secker & Warburg',
        }
        self.user = Mock(id='user_123')
        self.context = {'request': Mock(user=self.user)}

    def test_serialize_book(self):
        book = Book.objects.create(**self.book_data, added_by='user_123')
        serializer = BookSerializer(book)
        data = serializer.data

        self.assertEqual(data['isbn'], self.book_data['isbn'])
        self.assertEqual(data['title'], self.book_data['title'])
        self.assertEqual(data['author'], self.book_data['author'])
        self.assertEqual(data['category'], self.book_data['category'])
        self.assertEqual(data['publisher'], self.book_data['publisher'])
        self.assertEqual(data['added_by'], 'user_123')
        self.assertIn('id', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)

    def test_deserialize_book(self):
        serializer = BookSerializer(data=self.book_data, context=self.context)
        self.assertTrue(serializer.is_valid())
        book = serializer.save()

        self.assertEqual(book.isbn, self.book_data['isbn'])
        self.assertEqual(book.title, self.book_data['title'])
        self.assertEqual(book.author, self.book_data['author'])
        self.assertEqual(book.category, self.book_data['category'])
        self.assertEqual(book.publisher, self.book_data['publisher'])
        self.assertEqual(book.added_by, 'user_123')

    def test_readonly_fields(self):
        serializer = BookSerializer(
            data={
                **self.book_data,
                'id': 'custom_id',
                'added_by': 'user_456',
            },
            context=self.context,
        )
        self.assertTrue(serializer.is_valid())
        book = serializer.save()

        self.assertNotEqual(book.id, 'custom_id')
        self.assertNotEqual(book.added_by, 'user_456')
        self.assertEqual(book.added_by, 'user_123')


class BorrowedBookSerializerTestCase(TestCase):
    def setUp(self):
        self.book = Book.objects.create(
            isbn='9780061120084',
            title='To Kill a Mockingbird',
            author='Harper Lee',
            category='Fiction',
            publisher='J. B. Lippincott & Co.',
            added_by='user_123',
        )
        self.borrowed_book = BorrowedBook.objects.create(
            book=self.book,
            borrower='user_456',
            proposed_return_date=timezone.now() + timedelta(days=14),
        )

    def test_serialize_borrowed_book(self):
        serializer = BorrowedBookSerializer(self.borrowed_book)
        data = serializer.data

        self.assertIn('book', data)
        self.assertEqual(data['book']['id'], str(self.book.id))
        self.assertEqual(data['book']['title'], self.book.title)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertFalse(data['is_returned'])
        self.assertIsNone(data['actual_return_date'])
        self.assertIn('proposed_return_date', data)


class BorrowBookSerializerTestCase(TestCase):
    def test_valid_duration(self):
        serializer = BorrowBookSerializer(data={'duration': 14})
        self.assertTrue(serializer.is_valid())

    def test_invalid_duration(self):
        serializer = BorrowBookSerializer(data={'duration': 'invalid'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('duration', serializer.errors)

    def test_negative_duration(self):
        serializer = BorrowBookSerializer(data={'duration': -1})
        self.assertTrue(serializer.is_valid())  # Assuming negative durations are allowed; adjust if not


class UserSerializerTestCase(TestCase):
    def setUp(self):
        self.user_data = {
            'id': 'user_789',
            'email': 'test@example.com',
            'last_name': 'Doe',
            'first_name': 'John',
        }

    def test_serialize_user(self):
        serializer = UserSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())
        data = serializer.data

        self.assertEqual(data['id'], self.user_data['id'])
        self.assertEqual(data['email'], self.user_data['email'])
        self.assertEqual(data['last_name'], self.user_data['last_name'])
        self.assertEqual(data['first_name'], self.user_data['first_name'])

    def test_invalid_email(self):
        invalid_data = self.user_data.copy()
        invalid_data['email'] = 'invalid-email'
        serializer = UserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
