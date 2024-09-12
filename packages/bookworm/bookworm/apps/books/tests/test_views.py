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

from bookworm.apps.books.models import Book, BorrowedBook


class TestBookwormViews(TestCase):
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
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(self.regular_user)}')

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

        self.borrowed_book = BorrowedBook.objects.create(
            id='borrowed_to_kill_a_mockingbird',
            book=self.book1,
            borrower=self.regular_user,
            proposed_return_date=timezone.now() + timedelta(days=14),
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

    def test_book_list_api_view(self):
        response = self.client.get(reverse('book-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)  # Only one book is available
        self.assertEqual(response.data['data'][0]['id'], 'book_1984')

    def test_book_list_api_view_with_filters(self):
        response = self.client.get(reverse('book-list'), {'publishers': 'Signet Classic', 'categories': 'Fiction'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['id'], 'book_1984')

    def test_book_detail_api_view(self):
        response = self.client.get(reverse('book-detail', kwargs={'id': 'book_1984'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['id'], 'book_1984')
        self.assertIn('added_by', response.data['data'])

    def test_book_detail_api_view_nonexistent_book(self):
        response = self.client.get(reverse('book-detail', kwargs={'id': 'nonexistent_book'}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('django.conf.settings.BOOKCOURIER.publish_book_borrowed')
    def test_borrow_book_api_view(self, publish_book_borrowed):
        response = self.client.post(reverse('borrow-book', kwargs={'book_id': 'book_1984'}), {'duration': 14})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(BorrowedBook.objects.filter(book_id='book_1984', borrower=self.regular_user).exists())

        publish_book_borrowed.assert_called_once()

    @patch('django.conf.settings.BOOKCOURIER.publish_book_borrowed')
    def test_borrow_book_api_view_already_borrowed(self, publish_book_borrowed):
        response = self.client.post(
            reverse(
                'borrow-book',
                kwargs={
                    'book_id': 'book_to_kill_a_mockingbird',
                },
            ),
            {'duration': 14},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('book is already borrowed', response.data['error'])

        publish_book_borrowed.assert_not_called()

    def test_borrow_book_api_view_nonexistent_book(self):
        response = self.client.post(reverse('borrow-book', kwargs={'book_id': 'nonexistent_book'}), {'duration': 14})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('django.conf.settings.BOOKCOURIER.publish_book_returned')
    def test_return_book_api_view(self, publish_book_returned):
        response = self.client.post(reverse('return-book', kwargs={'book_id': 'book_to_kill_a_mockingbird'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        borrowed_book = BorrowedBook.objects.get(id='borrowed_to_kill_a_mockingbird')
        self.assertTrue(borrowed_book.is_returned)
        self.assertIsNotNone(borrowed_book.actual_return_date)
        publish_book_returned.assert_called_once()

    def test_return_book_api_view_not_borrowed(self):
        response = self.client.post(reverse('return-book', kwargs={'book_id': 'book_1984'}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('no active borrow record found', response.data['error'])

    def test_return_book_api_view_already_returned(self):
        self.borrowed_book.is_returned = True
        self.borrowed_book.save()
        response = self.client.post(reverse('return-book', kwargs={'book_id': 'book_to_kill_a_mockingbird'}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('no active borrow record found', response.data['error'])

    def test_book_list_api_view_all_borrowed(self):
        BorrowedBook.objects.create(
            id='borrowed_1984',
            book=self.book2,
            borrower=self.regular_user,
            proposed_return_date=timezone.now() + timedelta(days=14),
        )
        response = self.client.get(reverse('book-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 0)

    def test_borrow_book_api_view_invalid_duration(self):
        response = self.client.post(reverse('borrow-book', kwargs={'book_id': 'book_1984'}), {'duration': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
