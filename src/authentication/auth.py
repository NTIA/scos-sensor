import logging
import re

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from jwt import ExpiredSignatureError, InvalidSignatureError
from rest_framework import authentication, exceptions
from rest_framework.authentication import get_authorization_header

logger = logging.getLogger(__name__)

token_auth_enabled = (
    "rest_framework.authentication.TokenAuthentication"
    in settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]
)
oauth_jwt_authentication_enabled = (
    "authentication.auth.OAuthAPIJWTAuthentication"
    in settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]
)

oauth_session_authentication_enabled = (
    "authentication.auth.OAuthSessionAuthentication"
    in settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]
)


def jwt_request_has_required_role(request):
    if request.auth:
        if "authorities" in request.auth:
            if request.auth["authorities"]:
                authorities = request.auth["authorities"]
                return settings.REQUIRED_ROLE.upper() in authorities
    return False


def get_uid_from_dn(cert_dn):
    p = re.compile("UID=(.*?)(?:,|$)")
    match = p.search(cert_dn)
    if not match:
        raise Exception("No UID found in certificate!")
    uid_raw = match.group()
    # logger.debug(f"uid_raw = {uid_raw}")
    uid = uid_raw.split("=")[1].rstrip(",")
    # logger.debug(f"uid = {uid}")
    return uid


def validate_token(token, cert_uid):
    public_key = ""
    try:
        with open(settings.PATH_TO_JWT_PUBLIC_KEY) as public_key_file:
            public_key = public_key_file.read()
    except Exception as e:
        logger.error(e)
    if not public_key:
        error = exceptions.AuthenticationFailed(
            "Unable to get public key to decode jwt"
        )
        logger.error(error)
        raise error
    try:
        # decode JWT token
        # verifies jwt signature using RS256 algorithm and public key
        # requires exp claim to verify token is not expired
        # decodes and returns base64 encoded payload
        decoded_token = jwt.decode(
            token,
            public_key,
            verify=True,
            algorithms="RS256",
            options={"require": ["exp"], "verify_exp": True},
        )
        if decoded_token["userDetails"]["uid"] != cert_uid:
            # https://tools.ietf.org/id/draft-ietf-oauth-mtls-07.html#rfc.section.3
            token_uid = decoded_token["userDetails"]["uid"]
            logger.debug(f"token uid {token_uid} does not match cert uid {cert_uid}")
            raise Exception("JWT DN does not match client certificate DN!")
        return decoded_token
    except ExpiredSignatureError as e:
        logger.error(e)
        raise exceptions.AuthenticationFailed("Token is expired!")
    except InvalidSignatureError as e:
        logger.error(e)
        raise exceptions.AuthenticationFailed("Unable to verify token!")
    except Exception as e:
        logger.error(e)
        raise exceptions.AuthenticationFailed(f"Unable to decode token! {e}")


def get_or_create_user_from_token(decoded_token):
    jwt_username = decoded_token["user_name"]
    user_model = get_user_model()
    user = None
    try:
        user = user_model.objects.get(username=jwt_username)
    except user_model.DoesNotExist:
        user = user_model.objects.create_user(username=jwt_username)
        user.email = decoded_token["userDetails"]["email"]
        user.save()
    if decoded_token["authorities"]:
        authorities = decoded_token["authorities"]
        if settings.REQUIRED_ROLE.upper() in authorities:
            user.is_staff = True
            # user.is_superuser = True
        else:
            user.is_staff = False
        user.save()
    return user


class OAuthAPIJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = get_authorization_header(request)
        if not auth_header:
            logger.debug("no auth header")
            return None
        auth_header = auth_header.split()
        if len(auth_header) != 2:
            return None
        if auth_header[0].decode().lower() != "bearer":
            logger.debug("no JWT bearer token")
            return None  # attempt other configured authentication methods
        token = auth_header[1]
        # get JWT public key
        cert_dn = request.headers.get("X-Ssl-Client-Dn")
        if not cert_dn:
            raise exceptions.AuthenticationFailed("No client certificate DN found!")
        cert_uid = get_uid_from_dn(cert_dn)
        decoded_token = validate_token(token, cert_uid)
        user = get_or_create_user_from_token(decoded_token)
        logger.info("user from token: " + str(user.email))
        return (user, decoded_token)


class OAuthSessionAuthentication(authentication.BaseAuthentication):
    """
    Use OAuth session for authentication.
    """

    def authenticate(self, request):
        """
        Returns a `User` if the request session currently has a logged in user.
        Otherwise returns `None`.
        """

        if not "oauth_token" in request.session:
            return None

        token = request.session["oauth_token"]
        access_token = token["access_token"].encode("utf-8")
        cert_dn = request.headers.get("X-Ssl-Client-Dn")
        if not cert_dn:
            raise exceptions.AuthenticationFailed("No client certificate DN found!")
        cert_uid = get_uid_from_dn(cert_dn)
        try:
            decoded_token = validate_token(access_token, cert_uid)
            if "client_id" not in decoded_token:
                logger.debug("No client_id in token")
                raise exceptions.AuthenticationFailed("No client_id in token")
            decoded_client_id = decoded_token["client_id"]
            request_client_id = settings.CLIENT_ID
            if decoded_client_id != request_client_id:
                logger.debug(
                    f"client_id from token {decoded_client_id} does not match request client_id {request_client_id}"
                )
                # https://tools.ietf.org/html/draft-ietf-oauth-security-topics-16#section-2.3
                raise exceptions.AuthenticationFailed(
                    "Access token was not issued to this client!"
                )
        except Exception as error:
            del request.session["oauth_token"]
            raise error
        except:
            del request.session["oauth_token"]
        user = get_or_create_user_from_token(decoded_token)
        logger.info("user from token: " + str(user.email))
        return (user, decoded_token)
