from django.urls import path

from bookworm.apps.users.views import UserLoginAPIView, UserEnrollmentAPIView

urlpatterns = [
    path('users', UserEnrollmentAPIView.as_view(), name='user-register'),
    path('users/login', UserLoginAPIView.as_view(), name='user-login'),
]
