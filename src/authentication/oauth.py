import logging

from django.conf import settings
from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session

logger = logging.getLogger(__name__)


def get_oauth_token():
    """Returns OAuth access token."""
    try:
        logger.debug(settings.CLIENT_ID)
        logger.debug(settings.CLIENT_SECRET)
        logger.debug(settings.USER_NAME)
        logger.debug(settings.PASSWORD)

        logger.debug(settings.OAUTH_TOKEN_URL)
        logger.debug(settings.PATH_TO_CLIENT_CERT)
        logger.debug(settings.PATH_TO_VERIFY_CERT)
        verify_ssl = settings.CALLBACK_SSL_VERIFICATION
        if settings.CALLBACK_SSL_VERIFICATION:
            if settings.PATH_TO_VERIFY_CERT != "":
                verify_ssl = settings.PATH_TO_VERIFY_CERT

        logger.debug(verify_ssl)
        oauth = OAuth2Session(
            client=LegacyApplicationClient(client_id=settings.CLIENT_ID)
        )
        oauth.cert = settings.PATH_TO_CLIENT_CERT
        token = oauth.fetch_token(
            token_url=settings.OAUTH_TOKEN_URL,
            username=settings.USER_NAME,
            password=settings.PASSWORD,
            client_id=settings.CLIENT_ID,
            client_secret=settings.CLIENT_SECRET,
            verify=verify_ssl,
        )
        oauth.close()
        return token
    except Exception:
        raise


def get_oauth_client():
    """Returns Authorized OAuth Client (with authentication header token)."""
    try:
        token = get_oauth_token()
        client = OAuth2Session(settings.CLIENT_ID, token=token)
        client.cert = settings.PATH_TO_CLIENT_CERT
        return client
    except Exception:
        raise
