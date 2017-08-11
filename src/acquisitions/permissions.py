from rest_framework import permissions


class IsAdminOrOwnerOrReadOnly(permissions.BasePermission):
    """Only allow an admin or a acquisition's owner to edit it."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner or an admin
        user = request.user
        acquisition = view.queryset.first()
        if acquisition and acquisition.schedule_entry.owner == user:
            return True

        return user.is_staff

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner or an admin
        user = request.user
        return obj.schedule_entry.owner == user or user.is_staff
