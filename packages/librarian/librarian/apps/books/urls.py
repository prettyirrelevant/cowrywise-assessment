from django.urls import path

from librarian.apps.books.views import (
    DeleteBookAPIView,
    BooksCreateAPIView,
    EnrolledUsersAPIView,
    UnavailableBooksAPIView,
    UserBorrowedBooksAPIView,
)

urlpatterns = [
    path('users/enrolled', EnrolledUsersAPIView.as_view(), name='user-list'),
    path('users/borrowed-books', UserBorrowedBooksAPIView.as_view(), name='user-borrowed-book-list'),
    path('books', BooksCreateAPIView.as_view(), name='book-create'),
    path('books/unavailable', UnavailableBooksAPIView.as_view(), name='book-unavailable-list'),
    path('books/<str:id>/', DeleteBookAPIView.as_view(), name='book-delete'),
]
