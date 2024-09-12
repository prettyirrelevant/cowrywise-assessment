import datetime
from typing import TYPE_CHECKING

import shortuuid

from django.conf import settings
from django.utils import timezone

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView

from pagekeeper import FetchUsersRequest

from bookworm.common.responses import error_response, success_response
from bookworm.apps.books.models import Book, BorrowedBook
from bookworm.common.authentication import init_authentication_service
from bookworm.apps.books.serializers import BookSerializer, UserSerializer, DummySerializer, BorrowBookSerializer

if TYPE_CHECKING:
    from bookcourier import BookCourier


class BookListAPIView(GenericAPIView):
    queryset = Book.objects.get_queryset()
    serializer_class = BookSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        publishers = self.request.query_params.getlist('publishers')
        categories = self.request.query_params.getlist('categories')

        if publishers:
            qs = qs.filter(publisher__in=publishers)

        if categories:
            qs = qs.filter(category__in=categories)

        return qs.exclude(borrowing_records__is_returned=False)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'publishers',
                openapi.IN_QUERY,
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING),
                description='array of publishers to filter',
            ),
            openapi.Parameter(
                'categories',
                openapi.IN_QUERY,
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING),
                description='array of categories to filter',
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)


class BookDetailAPIView(GenericAPIView):
    lookup_field = 'id'
    serializer_class = BookSerializer
    queryset = Book.objects.get_queryset()

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        auth_service = init_authentication_service()
        response = auth_service.FetchUsers(FetchUsersRequest(ids=[instance.added_by]))
        added_by_user = response.users[0] if response.users else None

        data = serializer.data
        data['added_by'] = UserSerializer(added_by_user).data if added_by_user else None
        return success_response(data)


class BorrowBookAPIView(GenericAPIView):
    serializer_class = BorrowBookSerializer
    bookcourier: 'BookCourier' = settings.BOOKCOURIER

    def post(self, request, book_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        book = Book.objects.filter(id=book_id).first()
        if not book:
            return error_response(error='book not found', status_code=status.HTTP_404_NOT_FOUND)

        if not book.is_available():
            return error_response(error='book is already borrowed', status_code=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        duration = serializer.validated_data['duration']
        proposed_return_date = now + datetime.timedelta(days=duration)

        borrowed_book = BorrowedBook.objects.create(
            book=book,
            updated_at=now,
            created_at=now,
            is_returned=False,
            borrower=request.user.id,
            id=f'borrow_{shortuuid.uuid()}',
            proposed_return_date=proposed_return_date,
        )

        self.bookcourier.publish_book_borrowed(
            {
                'book_id': str(book.id),
                'id': str(borrowed_book.id),
                'created_at': now.isoformat(),
                'updated_at': now.isoformat(),
                'user_id': str(request.user.id),
                'proposed_return_date': proposed_return_date.isoformat(),
            }
        )

        return success_response(None)


class ReturnBookAPIView(APIView):
    bookcourier: 'BookCourier' = settings.BOOKCOURIER

    @swagger_auto_schema(responses={status.HTTP_200_OK: DummySerializer})
    def post(self, request, book_id):
        borrow_record = BorrowedBook.objects.filter(
            book_id=book_id,
            is_returned=False,
            borrower=request.user.id,
        ).first()

        if not borrow_record:
            return error_response('no active borrow record found for this book and user')

        now = timezone.now()

        borrow_record.is_returned = True
        borrow_record.actual_return_date = now
        borrow_record.save()

        self.bookcourier.publish_book_returned(actual_return_date=now.isoformat(), borrowed_book_id=borrow_record.id)
        return success_response(None)
