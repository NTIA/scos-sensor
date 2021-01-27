"""
OAuth 2 Views
https://requests-oauthlib.readthedocs.io/en/latest/examples/real_world_example.html
"""
import logging
import socket
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
from sensor.settings import (
    CLIENT_ID,
    CLIENT_SECRET,
    MOCK_RADIO,
    OAUTH_AUTHORIZATION_URL,
    OAUTH_TOKEN_URL,
    PATH_TO_CLIENT_CERT,
    PATH_TO_VERIFY_CERT,
    RUNNING_TESTS,
)

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
        CLIENT_ID, redirect_uri="https://" + settings.FQDN + reverse("oauth-callback")
    )
    logger.debug("OAUTH_AUTHORIZATION_URL = " + OAUTH_AUTHORIZATION_URL)
    authorization_url, state = authserver.authorization_url(OAUTH_AUTHORIZATION_URL)
    logger.debug("authorization_url = " + str(authorization_url))
    # State is used to prevent CSRF, keep this for later.
    request.session["oauth_state"] = state
    return HttpResponseRedirect(authorization_url)


@api_view(["GET"])
@permission_classes([AllowAny])
def oauth_login_callback(request):
    """ Step 3: Retrieving an access token.

    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    https://requests-oauthlib.readthedocs.io/en/latest/examples/real_world_example.html
    """
    authorization_host = urlparse(OAUTH_AUTHORIZATION_URL).hostname
    authorization_ip = socket.gethostbyname(authorization_host)
    request_origin_ip = request.headers["X-Forwarded-For"]
    if authorization_ip != request_origin_ip:
        if not RUNNING_TESTS and MOCK_RADIO:
            # calling sensor running on local docker container does not show correct request_origin_ip
            logger.debug("OAuth callback did not come from authserver")
        else:
            return Response(
                "OAuth callback did not come from authserver",
                status=status.HTTP_403_FORBIDDEN,
            )
    token_host = urlparse(OAUTH_TOKEN_URL).hostname
    if authorization_host != token_host:
        raise Exception(
            "OAUTH_AUTHORIZATION_URL and OAUTH_TOKEN_URL must use the same host!"
        )

    authserver = OAuth2Session(
        CLIENT_ID,
        state=request.session["oauth_state"],
        redirect_uri="https://" + settings.FQDN + reverse("oauth-callback"),
    )
    authserver.cert = PATH_TO_CLIENT_CERT
    logger.debug("OAUTH_TOKEN_URL = " + OAUTH_TOKEN_URL)
    logger.debug("authorization_response = " + request.build_absolute_uri())
    token = authserver.fetch_token(
        OAUTH_TOKEN_URL,
        client_secret=CLIENT_SECRET,
        authorization_response=request.build_absolute_uri(),
        verify=PATH_TO_VERIFY_CERT,
    )

    request.session["oauth_token"] = token
    del request.session["oauth_state"]  # state can only be used once
    return HttpResponseRedirect(reverse("api-root", kwargs=V1))
