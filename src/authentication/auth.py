import logging
import re
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions
from rest_framework.authentication import get_authorization_header

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
            logger.info("DN:" + cert_dn)
            cn = get_cn_from_dn(cert_dn)
            logger.info("Cert cn: " + cn)
            user_model = get_user_model()
            user = None
            try:
                user = user_model.objects.get(username=cn)
            except user_model.DoesNotExist:
                user = user_model.objects.create_user(username=cn)
                user.save()
            return user, None
        return None, None


def get_cn_from_dn(cert_dn):
    p = re.compile("CN=(.*?)(?:,|\+|$)")
    match = p.search(cert_dn)
    if not match:
        raise Exception("No CN found in certificate!")
    uid_raw = match.group()
    # logger.debug(f"uid_raw = {uid_raw}")
    uid = uid_raw.split("=")[1].rstrip(",")
    # logger.debug(f"uid = {uid}")
    return uid
