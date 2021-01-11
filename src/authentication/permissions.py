import json
import logging
import socket
from urllib.parse import urlparse

from django.conf import settings
from rest_framework import permissions

from sensor.settings import OAUTH_AUTHORIZATION_URL

from .auth import (
    decode_token,
    get_or_create_user_from_token,
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


def admin_permission(request):
    # permission = JWTRoleOrIsSuperuser()
    # return permission.has_permission(request, None)
    token = request.session["oauth_token"]
    logger.debug("token = " + json.dumps(token))
    access_token = token["access_token"].encode("utf-8")
    logger.debug("access_token = " + str(access_token))
    decoded_token = decode_token(access_token)
    # user = get_or_create_user_from_token(decoded_token)
    if oauth_jwt_authentication_enabled or oauth_session_authentication_enabled:
        if "authorities" in decoded_token:
            if decoded_token["authorities"]:
                authorities = decoded_token["authorities"]
                return settings.REQUIRED_ROLE.upper() in authorities
    if request.user.is_staff:
        return True
    return False


# class FromAuthServer(permissions.BasePermission):
#     message = "Request not from auth server"

#     def has_permission(self, request, view):
#         logger.debug("Checking FromAuthServer permission for request: " + str(request))
#         logger.debug("request.headers = " + str(request.headers))
#         logger.debug("request.META = " + str(request.META))
#         if not OAUTH_AUTHORIZATION_URL:
#             return False
#         result = urlparse(OAUTH_AUTHORIZATION_URL)
#         allowed_host_name = result.hostname
#         logger.debug("allowed_host_name = " + allowed_host_name)
#         allowed_ip = socket.gethostbyname(allowed_host_name)
#         logger.debug("allowed_ip = " + allowed_ip)
#         request_source_ip = request.META["REMOTE_ADDR"]
#         logger.debug("request_source_ip = " + request_source_ip)
#         return allowed_ip == request_source_ip
#         #return allowed_host_name.lower() == request_host_name.lower()
