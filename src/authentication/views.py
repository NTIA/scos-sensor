import logging

from django.conf import settings
from django.http.response import HttpResponseRedirect
from requests_oauthlib.oauth2_session import OAuth2Session
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny
from rest_framework.reverse import reverse

from sensor import V1
from sensor.settings import (
    CLIENT_ID,
    CLIENT_SECRET,
    OAUTH_AUTHORIZATION_URL,
    OAUTH_TOKEN_URL,
    PATH_TO_CLIENT_CERT,
    PATH_TO_VERIFY_CERT,
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

    return HttpResponseRedirect(reverse("api-root", kwargs=V1))
