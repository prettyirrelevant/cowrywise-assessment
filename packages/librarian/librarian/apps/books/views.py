from typing import TYPE_CHECKING

from django.conf import settings
from django.db.models import F
from django.db.models.functions import JSONObject
from django.contrib.postgres.aggregates import ArrayAgg

from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, CreateAPIView, GenericAPIView

from pagekeeper import FetchUsersRequest

from librarian.common.responses import success_response
from librarian.apps.books.models import Book, BorrowedBook
from librarian.common.authentication import init_authentication_service
from librarian.apps.books.serializers import BookSerializer, UserSerializer, DummySerializer, BorrowedBookSerializer

if TYPE_CHECKING:
    from bookcourier import BookCourier


class EnrolledUsersAPIView(ListAPIView):
    """Endpoint to fetch all users enrolled in the library."""

    serializer_class = UserSerializer

    def list(self, request, *args, **kwargs):
        auth_service = init_authentication_service()
        response = auth_service.FetchUsers(FetchUsersRequest())

        # remove admin users from the response since they dont akshually enroll
        users = [
            {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'id': user.id,
            }
            for user in response.users
            if not user.is_admin
        ]
        return success_response(users)


class DeleteBookAPIView(GenericAPIView):
    """Endpoint to remove a book from the catalogue."""

    lookup_field = 'id'
    queryset = Book.objects.get_queryset()
    bookcourier: 'BookCourier' = settings.BOOKCOURIER

    @swagger_auto_schema(responses={status.HTTP_200_OK: DummySerializer})
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.bookcourier.publish_book_removed(
            book_id=instance.id,
        )
        instance.delete()
        return success_response(None, status_code=status.HTTP_204_NO_CONTENT)


class BooksCreateAPIView(CreateAPIView):
    """Endpoint to create a new book."""

    serializer_class = BookSerializer
    queryset = Book.objects.get_queryset()
    bookcourier: 'BookCourier' = settings.BOOKCOURIER

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        self.bookcourier.publish_book_added(
            {
                'id': response.data['id'],
                'isbn': response.data['isbn'],
                'title': response.data['title'],
                'author': response.data['author'],
                'added_by': response.data['added_by'],
                'category': response.data['category'],
                'publisher': response.data['publisher'],
                'created_at': response.data['created_at'],
                'updated_at': response.data['updated_at'],
            }
        )
        return success_response(data=response.data, status_code=status.HTTP_201_CREATED)


class UnavailableBooksAPIView(ListAPIView):
    """Endpoint to fetch books that are not available for borrowing."""

    serializer_class = BorrowedBookSerializer
    queryset = BorrowedBook.objects.get_queryset()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success_response(response.data)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(is_returned=False)


class UserBorrowedBooksAPIView(APIView):
    """Endpoint to fetch users and the books they have borrowed."""

    def get_grouped_borrowed_books(self):
        return (
            BorrowedBook.objects.filter(is_returned=False)
            .select_related('book')
            .values('borrower')
            .annotate(
                borrowed_books=ArrayAgg(
                    JSONObject(
                        id=F('id'),
                        isbn=F('book__isbn'),
                        book_id=F('book__id'),
                        title=F('book__title'),
                        author=F('book__author'),
                        created_at=F('created_at'),
                        updated_at=F('updated_at'),
                        proposed_return_date=F('proposed_return_date'),
                    )
                )
            )
            .order_by('borrower')
        )

    def fetch_user_details(self, borrower_ids):
        auth_service = init_authentication_service()
        response = auth_service.FetchUsers(FetchUsersRequest(ids=borrower_ids))
        return {user.id: user for user in response.users}

    @swagger_auto_schema(responses={status.HTTP_200_OK: DummySerializer})
    def get(self, request):
        grouped_books = self.get_grouped_borrowed_books()
        borrower_ids = [item['borrower'] for item in grouped_books]
        user_details = self.fetch_user_details(borrower_ids)

        result = []
        for item in grouped_books:
            borrower_id = item['borrower']
            user = user_details.get(borrower_id)
            if user:
                result.append(
                    {
                        'user': {
                            'id': user.id,
                            'email': user.email,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                        },
                        'borrowed_books': item['borrowed_books'],
                    }
                )

        return success_response(result)
