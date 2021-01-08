from decimal import DivisionByZero

import jwt
import oauthlib
import pytest
import requests_mock
from django.test.testcases import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APISimpleTestCase, RequestsClient

from authentication.auth import oauth_session_authentication_enabled
from authentication.tests.test_jwt_auth import (
    PRIVATE_KEY,
    TEST_JWT_PUBLIC_KEY_FILE,
    get_token_payload,
)
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


@pytest.mark.django_db
def test_oauth_login_callback_bad_state():
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
        with pytest.raises(oauthlib.oauth2.rfc6749.errors.MismatchingStateError):
            client.get(f"{oauth_callback_url}?code=test_code&state=some_state")


@pytest.mark.django_db
def test_oauth_login_authorization_flow(live_server, settings):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE

    def auth_callback(request, context):
        if f"{request.scheme}://{request.hostname}{request.path}".startswith(
            OAUTH_AUTHORIZATION_URL
        ):
            query_start_index = request.path_url.find("?")
            query = request.path_url[query_start_index + 1 :]
            if "response_type=code" in query:
                if f"client_id={CLIENT_ID}" in query:
                    for query_param in query.split("&"):
                        if query_param.startswith("state="):
                            equals_index = query_param.find("=")
                            state = query_param[equals_index + 1 :]
                            _oauth_callback_url = reverse("oauth_callback")
                            context.headers = {
                                "Location": f"{live_server.url}{_oauth_callback_url}?code=test_code&state={state}"
                            }
        return ""

    client = RequestsClient()
    token_payload = get_token_payload()
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    with requests_mock.Mocker(real_http=True) as m:
        m.post(OAUTH_TOKEN_URL, json={"access_token": utf8_bytes})
        url_redirect = (
            OAUTH_AUTHORIZATION_URL + "?response_type=code&client_id=" + CLIENT_ID
        )
        m.get(url_redirect, status_code=307, text=auth_callback)
        login_path = reverse("login")
        url = f"{live_server.url}{login_path}"
        response = client.get(url, allow_redirects=False)  # sensor login
        assert response.is_redirect == True
        assert response.is_permanent_redirect == False
        response = client.get(  # authserver login
            response.headers["Location"], allow_redirects=False
        )
        assert response.is_redirect == True
        assert response.is_permanent_redirect == False
        assert reverse("oauth_callback") in response.headers["Location"]
        response = client.get(  # sensor callback
            response.headers["Location"], allow_redirects=False
        )
        assert response.is_redirect == True
        assert response.is_permanent_redirect == False
        location = response.headers["Location"]
        response = client.get(  # sensor home page
            f"{live_server.url}{location}", allow_redirects=False
        )
        assert response.is_redirect == False
        assert response.is_permanent_redirect == False
        assert response.status_code == 200
