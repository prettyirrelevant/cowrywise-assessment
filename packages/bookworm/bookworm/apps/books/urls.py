from django.urls import path

from bookworm.apps.books.views import BookListAPIView, BookDetailAPIView, BorrowBookAPIView, ReturnBookAPIView

urlpatterns = [
    path('books', BookListAPIView.as_view(), name='book-list'),
    path('books/<str:book_id>/borrow', BorrowBookAPIView.as_view(), name='borrow-book'),
    path('books/<str:book_id>/return', ReturnBookAPIView.as_view(), name='return-book'),
    path('books/<str:id>', BookDetailAPIView.as_view(), name='book-detail'),
]
