from rest_framework import permissions


class IsAdminOrSelf(permissions.BasePermission):
    """Allow an admin to view all users, but a user to only view themselves."""

    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.is_admin
