from datetime import timedelta
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

import grpc

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

from pagekeeper import PageKeeperService, add_PageKeeperServicer_to_server
from pagekeeper.config import AppConfig
from pagekeeper.helpers import create_token, hash_password, initialize_database

from librarian.apps.books.models import Book, BorrowedBook


class TestViews(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.config = AppConfig(db_name='test_pagekeeper')
        cls.auth_database = initialize_database(url=cls.config.MONGODB_URL, db_name=cls.config.DATABASE_NAME)

        cls.server = grpc.server(ThreadPoolExecutor(max_workers=10))
        add_PageKeeperServicer_to_server(PageKeeperService(cls.auth_database, cls.config), cls.server)
        cls.server.add_insecure_port(settings.AUTHENTICATION_SERVER_URL)
        cls.server.start()

        cls.admin_user = cls.create_user('admin@library.com', 'Jane', 'Doe', is_admin=True)
        cls.regular_user = cls.create_user('user@library.com', 'John', 'Smith')

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'auth_database'):
            cls.auth_database.client.drop_database(cls.config.DATABASE_NAME)

        if hasattr(cls, 'server'):
            cls.server.stop(grace=None)

        super().tearDownClass()

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(self.admin_user, is_admin=True)}')

        self.book1 = Book.objects.create(
            id='book_to_kill_a_mockingbird',
            title='To Kill a Mockingbird',
            author='Harper Lee',
            added_by=self.admin_user,
            isbn='9780446310789',
            category='Fiction',
            publisher='Grand Central Publishing',
        )
        self.book2 = Book.objects.create(
            id='book_1984',
            title='1984',
            author='George Orwell',
            added_by=self.admin_user,
            isbn='9780451524935',
            category='Fiction',
            publisher='Signet Classic',
        )

        self.borrowed_book1 = BorrowedBook.objects.create(
            id='borrowed_to_kill_a_mockingbird',
            book=self.book1,
            borrower=self.regular_user,
            proposed_return_date=timezone.now() + timedelta(days=14),
        )
        self.borrowed_book2 = BorrowedBook.objects.create(
            id='borrowed_1984',
            book=self.book2,
            borrower=self.regular_user,
            proposed_return_date=timezone.now() - timedelta(days=1),
        )

    @classmethod
    def create_user(cls, email, first_name, last_name, is_admin=False):
        user_id = f"user_{'admin' if is_admin else 'regular'}_{email.split('@')[0]}"
        cls.auth_database.users.insert_one(
            {
                'email': email,
                'user_id': user_id,
                'is_admin': is_admin,
                'last_name': last_name,
                'first_name': first_name,
                'hashed_password': hash_password('password123'),
            }
        )
        return user_id

    def get_token(self, user_id, is_admin=False):
        return create_token(
            user_id=user_id,
            is_admin=is_admin,
            secret=self.config.SECRET_KEY,
            expiration=self.config.ACCESS_TOKEN_EXPIRATION,
        )

    def test_enrolled_users_api_view(self):
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)  # Only non-admin users
        self.assertEqual(response.data['data'][0]['id'], self.regular_user)
        self.assertEqual(response.data['data'][0]['email'], 'user@library.com')

    def test_delete_book_api_view(self):
        # Test with non-admin user
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(self.regular_user)}')
        response = self.client.delete(reverse('book-delete', kwargs={'id': 'book_to_kill_a_mockingbird'}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test with admin user
        with patch('django.conf.settings.BOOKCOURIER.publish_book_removed') as mock_publish_book_removed:
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(self.admin_user, is_admin=True)}')
            response = self.client.delete(reverse('book-delete', kwargs={'id': 'book_to_kill_a_mockingbird'}))
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            self.assertFalse(Book.objects.filter(id='book_to_kill_a_mockingbird').exists())

        mock_publish_book_removed.assert_called_once()

    def test_books_create_api_view(self):
        book_data = {
            'title': 'Pride and Prejudice',
            'author': 'Jane Austen',
            'isbn': '9780141439518',
            'category': 'Fiction',
            'publisher': 'Penguin Classics',
        }

        # Test with non-admin user
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(self.regular_user)}')
        response = self.client.post(reverse('book-create'), book_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test with admin user
        with patch('django.conf.settings.BOOKCOURIER.publish_book_added') as mock_publish_book_added:
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(self.admin_user, is_admin=True)}')
            response = self.client.post(reverse('book-create'), book_data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Book.objects.count(), 3)
            new_book = Book.objects.get(isbn='9780141439518')
            self.assertEqual(new_book.title, 'Pride and Prejudice')

        mock_publish_book_added.assert_called_once()

    def test_unavailable_books_api_view(self):
        response = self.client.get(reverse('book-unavailable-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)  # Only overdue books
        self.assertEqual(response.data['data'][0]['book']['id'], 'book_1984')

    def test_user_borrowed_books_api_view(self):
        response = self.client.get(reverse('user-borrowed-book-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)  # One user with borrowed books

        user_data = response.data['data'][0]
        self.assertEqual(user_data['user']['id'], self.regular_user)
        self.assertEqual(user_data['user']['email'], 'user@library.com')
        self.assertEqual(len(user_data['borrowed_books']), 2)

    def test_user_borrowed_books_api_view_empty(self):
        # Return all borrowed books
        BorrowedBook.objects.all().delete()

        response = self.client.get(reverse('user-borrowed-book-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 0)

    def test_unavailable_books_api_view_all_available(self):
        # make all books available
        BorrowedBook.objects.all().delete()

        response = self.client.get(reverse('book-unavailable-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 0)

    def test_books_create_api_view_invalid_data(self):
        invalid_book_data = {
            'title': '',
            'isbn': '1234',
            'category': 'Fiction',
            'author': 'Jane Austen',
            'publisher': 'Penguin Classics',
        }

        response = self.client.post(reverse('book-create'), invalid_book_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_nonexistent_book(self):
        response = self.client.delete(reverse('book-delete', kwargs={'id': 'book_nonexistent'}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
