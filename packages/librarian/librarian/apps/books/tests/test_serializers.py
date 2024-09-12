from datetime import timedelta

import shortuuid

from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APIRequestFactory

from librarian.apps.books.models import Book, BorrowedBook
from librarian.apps.books.serializers import BookSerializer, BorrowedBookSerializer


class BookSerializerTest(TestCase):
    def setUp(self):
        self.book_data = {
            'isbn': '9780061120084',
            'title': 'To Kill a Mockingbird',
            'author': 'Harper Lee',
            'category': 'Fiction',
            'publisher': 'HarperCollins',
        }
        self.user_id = f'user_{shortuuid.uuid()}'
        self.serializer_context = {'request': APIRequestFactory().post('/books/')}
        self.serializer_context['request'].user = type('User', (), {'id': self.user_id})()

    def test_book_serializer_create(self):
        serializer = BookSerializer(data=self.book_data, context=self.serializer_context)
        self.assertTrue(serializer.is_valid())
        book = serializer.save()

        self.assertTrue(book.id.startswith('book_'))
        self.assertEqual(book.added_by, self.user_id)
        self.assertEqual(book.isbn, self.book_data['isbn'])
        self.assertEqual(book.title, self.book_data['title'])
        self.assertEqual(book.author, self.book_data['author'])
        self.assertEqual(book.category, self.book_data['category'])
        self.assertEqual(book.publisher, self.book_data['publisher'])

    def test_book_serializer_read_only_fields(self):
        book = Book.objects.create(id=f'book_{shortuuid.uuid()}', added_by=self.user_id, **self.book_data)
        serializer = BookSerializer(book)
        data = serializer.data

        self.assertIn('id', data)
        self.assertIn('added_by', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)

    def test_book_serializer_update(self):
        book = Book.objects.create(id=f'book_{shortuuid.uuid()}', added_by=self.user_id, **self.book_data)
        updated_data = {
            'title': 'Updated Title',
            'author': 'Updated Author',
        }
        serializer = BookSerializer(book, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_book = serializer.save()

        self.assertEqual(updated_book.title, 'Updated Title')
        self.assertEqual(updated_book.author, 'Updated Author')
        self.assertEqual(updated_book.id, book.id)
        self.assertEqual(updated_book.added_by, book.added_by)


class BorrowedBookSerializerTest(TestCase):
    def setUp(self):
        self.user_id = f'user_{shortuuid.uuid()}'
        self.book = Book.objects.create(
            id=f'book_{shortuuid.uuid()}',
            added_by=self.user_id,
            isbn='9780061120084',
            title='To Kill a Mockingbird',
            author='Harper Lee',
            category='Fiction',
            publisher='HarperCollins',
        )
        self.borrowed_book = BorrowedBook.objects.create(
            id=f'borrowed_{shortuuid.uuid()}',
            book=self.book,
            borrower=self.user_id,
            proposed_return_date=timezone.now() + timedelta(days=14),
        )

    def test_borrowed_book_serializer(self):
        serializer = BorrowedBookSerializer(self.borrowed_book)
        data = serializer.data

        self.assertIn('book', data)
        self.assertIn('is_returned', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIn('actual_return_date', data)
        self.assertIn('proposed_return_date', data)

        self.assertEqual(data['book']['id'], self.book.id)
        self.assertEqual(data['book']['title'], self.book.title)
        self.assertFalse(data['is_returned'])
        self.assertIsNone(data['actual_return_date'])
