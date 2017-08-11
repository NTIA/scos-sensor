from rest_framework import permissions


class IsAdminOrOwnerOrReadOnly(permissions.BasePermission):
    """Only allow an admin or a schedule entry's owner to edit it."""

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner or an admin
        return obj.owner == request.user or request.user.is_admin
