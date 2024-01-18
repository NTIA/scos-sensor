from rest_framework import permissions


class IsSuperuser(permissions.BasePermission):
    message = "User is not superuser"

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        return False
