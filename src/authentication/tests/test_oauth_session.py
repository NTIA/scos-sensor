import pytest
import requests_mock
from django.test.testcases import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APISimpleTestCase

from authentication.auth import oauth_session_authentication_enabled
from sensor import V1
from sensor.settings import CLIENT_ID, OAUTH_AUTHORIZATION_URL, OAUTH_TOKEN_URL

pytestmark = pytest.mark.skipif(
    not oauth_session_authentication_enabled,
    reason="OAuth JWT authentication is not enabled!",
)


@pytest.mark.django_db
def test_oauth_login_view():
    client = APIClient()
    response = client.get(reverse("login"))
    assert response.wsgi_request.session["oauth_state"]
    url_redirect = (
        OAUTH_AUTHORIZATION_URL
        + "?response_type=code&client_id="
        + CLIENT_ID
        + "&state="
        + response.wsgi_request.session["oauth_state"]
    )
    SimpleTestCase().assertRedirects(
        response, url_redirect, fetch_redirect_response=False
    )


@pytest.mark.django_db
def test_oauth_login_callback():
    test_state = "test_state"
    test_token = "test_access_token"
    client = APIClient()
    session = client.session
    session["oauth_state"] = test_state
    session.save()
    response = None
    with requests_mock.Mocker() as m:
        m.post(OAUTH_TOKEN_URL, json={"access_token": test_token})
        oauth_callback_url = reverse("oauth_callback")
        response = client.get(f"{oauth_callback_url}?code=test_code&state={test_state}")
    assert response.wsgi_request.session["oauth_token"]["access_token"] == test_token
    SimpleTestCase().assertRedirects(
        response, reverse("api-root", kwargs=V1), fetch_redirect_response=False
    )
