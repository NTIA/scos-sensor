import logging

from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session

from sensor import settings

logger = logging.getLogger(__name__)



def get_access_token():
    """Returns Location object JSON if set or None and logs an error."""
    try:
        logger.debug(settings.CLIENT_ID)
        logger.debug(settings.CLIENT_SECRET)
        logger.debug(settings.USER_NAME)
        logger.debug(settings.PASSWORD)

        logger.debug(settings.OAUTH_TOKEN_URL)
        logger.debug(settings.OAUTH_PATH_TO_CLIENT_CERT)
        logger.debug(settings.OAUTH_PATH_TO_VERIFY_CERT)

        oauth = OAuth2Session(client=LegacyApplicationClient(client_id=settings.CLIENT_ID))
        oauth.cert = settings.OAUTH_PATH_TO_CLIENT_CERT
        token = oauth.fetch_token(
            token_url=settings.OAUTH_TOKEN_URL,
            username=settings.USER_NAME, password=settings.PASSWORD,
            client_id=settings.CLIENT_ID, client_secret=settings.CLIENT_SECRET,
            verify=False
        )
        oauth.close()
        logger.debug("Response from oauth.fetch_token: " + str(token))
        return token
    except Exception:
        raise

def get_oauth_client():
    """Returns Location object JSON if set or None and logs an error."""
    try:
        token = get_access_token()
        client = OAuth2Session(settings.CLIENT_ID, token=token)
        client.cert = settings.OAUTH_PATH_TO_CLIENT_CERT
        return client
    except Exception:
        raise
