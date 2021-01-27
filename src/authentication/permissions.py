import logging

from rest_framework import permissions

from .auth import (
    jwt_request_has_required_role,
    oauth_jwt_authentication_enabled,
    oauth_session_authentication_enabled,
)

logger = logging.getLogger(__name__)


class JWTRoleOrIsSuperuser(permissions.BasePermission):
    message = "User missing required role"

    def has_permission(self, request, view):
        if (
            oauth_jwt_authentication_enabled or oauth_session_authentication_enabled
        ) and jwt_request_has_required_role(request):
            return True
        if request.user.is_superuser:
            return True
        return False
