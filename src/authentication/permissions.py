from rest_framework import permissions


class RequiredJWTRolePermissionOrIsSuperuser(permissions.BasePermission):
    message = "User missing required role"

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        return False
