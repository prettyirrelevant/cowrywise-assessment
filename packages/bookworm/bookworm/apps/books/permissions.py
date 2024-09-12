from rest_framework.permissions import BasePermission


class IsEnrolledUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and not request.user.is_admin)
