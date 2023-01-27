import logging
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions

logger = logging.getLogger(__name__)

token_auth_enabled = (
    "rest_framework.authentication.TokenAuthentication"
    in settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]
)
certificate_authentication_enabled = (
    "authentication.auth.CertificateAuthentication"
    in settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]
)


class CertificateAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        logger.debug("Authenticating certificate.")
        cert_dn = request.headers.get("X-Ssl-Client-Dn")
        if cert_dn:
            user_model = get_user_model()
            try:
                cn = get_cn_from_dn(cert_dn)
                user = user_model.objects.get(username=cn)
            except user_model.DoesNotExist:
                raise exceptions.AuthenticationFailed("No matching username found!")
            except Exception:
                raise exceptions.AuthenticationFailed(
                    "Error occurred during certificate authentication!"
                )
            return user, None
        return None, None


def get_cn_from_dn(cert_dn):
    p = re.compile(r"CN=(.*?)(?:,|\+|$)")
    match = p.search(cert_dn)
    if not match:
        raise Exception("No CN found in certificate!")
    uid_raw = match.group()
    uid = uid_raw.split("=")[1].rstrip(",")
    return uid
