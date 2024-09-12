from django.urls import path

from librarian.apps.users.views import AdminRegistrationAPIView, AdminAuthenticationAPIView

urlpatterns = [
    path('users', AdminRegistrationAPIView.as_view(), name='user-register'),
    path('users/login', AdminAuthenticationAPIView.as_view(), name='user-login'),
]
