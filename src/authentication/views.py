"""
OAuth 2 Views
https://requests-oauthlib.readthedocs.io/en/latest/examples/real_world_example.html
"""
import base64
import logging
from urllib.parse import urlparse

from django.conf import settings
from django.http.response import HttpResponseRedirect
from requests_oauthlib.oauth2_session import OAuth2Session
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse

from sensor import V1

from .models import User
from .serializers import UserDetailsSerializer

logger = logging.getLogger(__name__)


class UserDetailsListView(ListCreateAPIView):
    """View user details and create users."""

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserDetailsSerializer


class UserDetailsView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailsSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def oauth_login_view(request):
    """
    Step 1: User Authorization.

    Redirect the user/resource owner to the OAuth provider (i.e. Github)
    using an URL with a few key OAuth parameters.

    # Step 2: User authorization, this happens on the provider.

    https://requests-oauthlib.readthedocs.io/en/latest/examples/real_world_example.html
    """
    authserver = OAuth2Session(
        settings.CLIENT_ID,
        redirect_uri="https://" + settings.FQDN + reverse("oauth-callback"),
    )
    logger.debug("OAUTH_AUTHORIZATION_URL = " + settings.OAUTH_AUTHORIZATION_URL)
    authorization_url, state = authserver.authorization_url(
        settings.OAUTH_AUTHORIZATION_URL
    )
    logger.debug("authorization_url = " + str(authorization_url))
    # State is used to prevent CSRF, keep this for later.
    request.session["oauth_state"] = state
    return HttpResponseRedirect(authorization_url)


# def log_fetch_token(response):
#     request = response.request
#     url = request.url
#     body = request.body
#     headers = request.headers
#     logger.debug(f"fetch token body = {body}")
#     logger.debug(f"fetch_token url = {url}")
#     for key, value in headers.items():
#         logger.debug(f"fetch_token header {key} = {value}")
#     auth_header = request.headers["Authorization"]
#     auth_method = auth_header.split()[0]
#     logger.debug(f"auth method = {auth_method.lower()}")
#     basic_auth_encode = auth_header.split()[1]
#     basic_auth_decode = base64.b64decode(basic_auth_encode)
#     logger.debug(f"decoded auth header = {basic_auth_decode.decode()}")
#     logger.debug("-------response-----------")
#     logger.debug(f"response.url = {response.url}")
#     logger.debug(f"response.text = {response.text}")
#     return response


@api_view(["GET"])
@permission_classes([AllowAny])
def oauth_login_callback(request):
    """Step 3: Retrieving an access token.

    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    https://requests-oauthlib.readthedocs.io/en/latest/examples/real_world_example.html
    """
    if not "oauth_state" in request.session:
        return Response(
            "'oauth_state' missing from session", status=status.HTTP_403_FORBIDDEN
        )
    state = request.session["oauth_state"]
    del request.session["oauth_state"]  # state can only be used once
    authorization_host = urlparse(settings.OAUTH_AUTHORIZATION_URL).hostname
    token_host = urlparse(settings.OAUTH_TOKEN_URL).hostname
    if authorization_host != token_host:
        raise Exception(
            "OAUTH_AUTHORIZATION_URL and OAUTH_TOKEN_URL must use the same host!"
        )

    authserver = OAuth2Session(
        settings.CLIENT_ID,
        state=state,
        redirect_uri="https://" + settings.FQDN + reverse("oauth-callback"),
    )
    authserver.cert = settings.PATH_TO_CLIENT_CERT
    logger.debug("OAUTH_TOKEN_URL = " + settings.OAUTH_TOKEN_URL)
    logger.debug("authorization_response = " + request.build_absolute_uri())
    # authserver.register_compliance_hook("access_token_response", log_fetch_token)
    token = authserver.fetch_token(
        settings.OAUTH_TOKEN_URL,
        client_secret=settings.CLIENT_SECRET,
        authorization_response=request.build_absolute_uri(),
        verify=settings.PATH_TO_VERIFY_CERT,
    )

    request.session["oauth_token"] = token
    return HttpResponseRedirect(reverse("api-root", kwargs=V1))
