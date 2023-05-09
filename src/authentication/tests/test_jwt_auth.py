import base64
import json
import os
import secrets
from datetime import datetime, timedelta
from tempfile import NamedTemporaryFile

import jwt
import pytest
from rest_framework.reverse import reverse
from rest_framework.test import RequestsClient

from authentication.auth import oauth_jwt_authentication_enabled
from authentication.models import User
from authentication.tests.utils import get_test_public_private_key
from sensor import V1

pytestmark = pytest.mark.skipif(
    not oauth_jwt_authentication_enabled,
    reason="OAuth JWT authentication is not enabled!",
)


jwt_content_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "jwt_content_example.json"
)
with open(jwt_content_file) as token_file:
    TOKEN_CONTENT = json.load(token_file)

BAD_PRIVATE_KEY, BAD_PUBLIC_KEY = get_test_public_private_key()

one_min = timedelta(minutes=1)
one_day = timedelta(days=1)


def get_token_payload(authorities=["ROLE_MANAGER"], exp=None, client_id=None):
    token_payload = TOKEN_CONTENT.copy()
    current_datetime = datetime.now()
    if not exp:
        token_payload["exp"] = (current_datetime + one_day).timestamp()
    else:
        token_payload["exp"] = exp
    token_payload["userDetails"]["lastlogin"] = (current_datetime - one_day).timestamp()
    token_payload["userDetails"]["authorities"] = []
    for authority in authorities:
        token_payload["userDetails"]["authorities"].append({"authority": authority})
    token_payload["userDetails"]["enabled"] = True
    token_payload["authorities"] = authorities
    if client_id:
        token_payload["client_id"] = client_id
    return token_payload


def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "X-Ssl-Client-Dn": f"CN=Test,OU=Test,O=Test,L=Test,ST=Test,C=Test",
    }


@pytest.mark.django_db
def test_no_token_unauthorized(live_server):
    client = RequestsClient()
    response = client.get(f"{live_server.url}")
    assert response.status_code == 403


@pytest.mark.django_db
def test_token_no_roles_unauthorized(live_server, jwt_keys):
    token_payload = get_token_payload(authorities=[])
    encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(encoded))
    assert response.status_code == 403
    assert response.json()["detail"] == "User missing required role"


@pytest.mark.django_db
def test_token_role_manager_accepted(live_server, jwt_keys):
    token_payload = get_token_payload()
    encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(encoded))
    assert response.status_code == 200


def test_bad_token_forbidden(live_server):
    client = RequestsClient()
    token = (
        secrets.token_urlsafe(28)
        + "."
        + secrets.token_urlsafe(679)
        + "."
        + secrets.token_urlsafe(525)
    )
    response = client.get(f"{live_server.url}", headers=get_headers(token))
    print(f"headers: {response.request.headers}")
    assert response.status_code == 403
    assert "Unable to decode token!" in response.json()["detail"]


@pytest.mark.django_db
def test_token_expired_1_day_forbidden(live_server, jwt_keys):
    current_datetime = datetime.now()
    token_payload = get_token_payload(exp=(current_datetime - one_day).timestamp())
    encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(encoded))
    assert response.status_code == 403
    assert response.json()["detail"] == "Token is expired!"


@pytest.mark.django_db
def test_bad_private_key_forbidden(live_server):
    token_payload = get_token_payload()
    encoded = jwt.encode(
        token_payload, str(BAD_PRIVATE_KEY.decode("utf-8")), algorithm="RS256"
    )
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(encoded))
    assert response.status_code == 403
    assert response.json()["detail"] == "Unable to verify token!"


@pytest.mark.django_db
def test_bad_public_key_forbidden(settings, live_server, jwt_keys):
    with NamedTemporaryFile() as jwt_public_key_file:
        jwt_public_key_file.write(BAD_PUBLIC_KEY)
        jwt_public_key_file.flush()
        settings.PATH_TO_JWT_PUBLIC_KEY = jwt_public_key_file.name
        token_payload = get_token_payload()
        encoded = jwt.encode(
            token_payload, str(jwt_keys.private_key), algorithm="RS256"
        )
        client = RequestsClient()
        response = client.get(f"{live_server.url}", headers=get_headers(encoded))
        assert response.status_code == 403
        assert response.json()["detail"] == "Unable to verify token!"


@pytest.mark.django_db
def test_token_expired_1_min_forbidden(live_server, jwt_keys):
    current_datetime = datetime.now()
    token_payload = get_token_payload(exp=(current_datetime - one_min).timestamp())
    encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(encoded))
    assert response.status_code == 403
    assert response.json()["detail"] == "Token is expired!"


@pytest.mark.django_db
def test_token_expires_in_1_min_accepted(live_server, jwt_keys):
    current_datetime = datetime.now()
    token_payload = get_token_payload(exp=(current_datetime + one_min).timestamp())
    encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(encoded))
    assert response.status_code == 200


@pytest.mark.django_db
def test_token_role_user_forbidden(live_server, jwt_keys):
    token_payload = get_token_payload(authorities=["ROLE_USER"])
    encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(encoded))
    assert response.status_code == 403
    assert response.json()["detail"] == "User missing required role"


@pytest.mark.django_db
def test_token_role_user_required_role_accepted(settings, live_server, jwt_keys):
    settings.REQUIRED_ROLE = "ROLE_USER"
    token_payload = get_token_payload(authorities=["ROLE_USER"])
    encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(encoded))
    assert response.status_code == 200


@pytest.mark.django_db
def test_token_multiple_roles_accepted(live_server, jwt_keys):
    token_payload = get_token_payload(
        authorities=["ROLE_MANAGER", "ROLE_USER", "ROLE_ITS"]
    )
    encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(encoded))
    assert response.status_code == 200


@pytest.mark.django_db
def test_token_mulitple_roles_forbidden(live_server, jwt_keys):
    token_payload = get_token_payload(
        authorities=["ROLE_SENSOR", "ROLE_USER", "ROLE_ITS"]
    )
    encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(encoded))
    assert response.status_code == 403


@pytest.mark.django_db
def test_urls_unauthorized(live_server, jwt_keys):
    token_payload = get_token_payload(authorities=["ROLE_USER"])
    encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
    client = RequestsClient()
    headers = get_headers(encoded)

    capabilities = reverse("capabilities", kwargs=V1)
    response = client.get(f"{live_server.url}{capabilities}", headers=headers)
    assert response.status_code == 403

    schedule_list = reverse("schedule-list", kwargs=V1)
    response = client.get(f"{live_server.url}{schedule_list}", headers=headers)
    assert response.status_code == 403

    status = reverse("status", kwargs=V1)
    response = client.get(f"{live_server.url}{status}", headers=headers)
    assert response.status_code == 403

    task_root = reverse("task-root", kwargs=V1)
    response = client.get(f"{live_server.url}{task_root}", headers=headers)
    assert response.status_code == 403

    task_results_overview = reverse("task-results-overview", kwargs=V1)
    response = client.get(f"{live_server.url}{task_results_overview}", headers=headers)
    assert response.status_code == 403

    upcoming_tasks = reverse("upcoming-tasks", kwargs=V1)
    response = client.get(f"{live_server.url}{upcoming_tasks}", headers=headers)
    assert response.status_code == 403

    user_list = reverse("user-list", kwargs=V1)
    response = client.get(f"{live_server.url}{user_list}", headers=headers)
    assert response.status_code == 403


@pytest.mark.django_db
def test_urls_authorized(live_server, jwt_keys):
    token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
    encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
    client = RequestsClient()
    headers = get_headers(encoded)

    capabilities = reverse("capabilities", kwargs=V1)
    response = client.get(f"{live_server.url}{capabilities}", headers=headers)
    assert response.status_code == 200

    schedule_list = reverse("schedule-list", kwargs=V1)
    response = client.get(f"{live_server.url}{schedule_list}", headers=headers)
    assert response.status_code == 200

    status = reverse("status", kwargs=V1)
    response = client.get(f"{live_server.url}{status}", headers=headers)
    assert response.status_code == 200

    task_root = reverse("task-root", kwargs=V1)
    response = client.get(f"{live_server.url}{task_root}", headers=headers)
    assert response.status_code == 200

    task_results_overview = reverse("task-results-overview", kwargs=V1)
    response = client.get(f"{live_server.url}{task_results_overview}", headers=headers)
    assert response.status_code == 200

    upcoming_tasks = reverse("upcoming-tasks", kwargs=V1)
    response = client.get(f"{live_server.url}{upcoming_tasks}", headers=headers)
    assert response.status_code == 200

    user_list = reverse("user-list", kwargs=V1)
    response = client.get(f"{live_server.url}{user_list}", headers=headers)
    assert response.status_code == 200


@pytest.mark.django_db
def test_user_cannot_view_user_detail(live_server, jwt_keys):
    sensor01_token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
    encoded = jwt.encode(
        sensor01_token_payload, str(jwt_keys.private_key), algorithm="RS256"
    )
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(encoded))
    assert response.status_code == 200

    sensor02_token_payload = get_token_payload(authorities=["ROLE_USER"])
    sensor02_token_payload["user_name"] = "sensor02"
    encoded = jwt.encode(
        sensor02_token_payload, str(jwt_keys.private_key), algorithm="RS256"
    )
    client = RequestsClient()

    sensor01_user = User.objects.get(username=sensor01_token_payload["user_name"])
    kws = {"pk": sensor01_user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    response = client.get(
        f"{live_server.url}{user_detail}", headers=get_headers(encoded)
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_user_cannot_view_user_detail_role_change(live_server, jwt_keys):
    sensor01_token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
    encoded = jwt.encode(
        sensor01_token_payload, str(jwt_keys.private_key), algorithm="RS256"
    )
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(encoded))
    assert response.status_code == 200

    token_payload = get_token_payload(authorities=["ROLE_USER"])
    encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
    client = RequestsClient()

    sensor01_user = User.objects.get(username=sensor01_token_payload["user_name"])
    kws = {"pk": sensor01_user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    response = client.get(
        f"{live_server.url}{user_detail}", headers=get_headers(encoded)
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_view_user_detail(live_server, jwt_keys):
    token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
    encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
    client = RequestsClient()
    headers = get_headers(encoded)
    response = client.get(f"{live_server.url}", headers=headers)
    assert response.status_code == 200

    sensor01_user = User.objects.get(username=token_payload["user_name"])
    kws = {"pk": sensor01_user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    response = client.get(f"{live_server.url}{user_detail}", headers=headers)
    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_can_view_other_user_detail(live_server, jwt_keys):
    sensor01_token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
    encoded = jwt.encode(
        sensor01_token_payload, str(jwt_keys.private_key), algorithm="RS256"
    )
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(encoded))
    assert response.status_code == 200

    sensor02_token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
    sensor02_token_payload["user_name"] = "sensor02"
    encoded = jwt.encode(
        sensor02_token_payload, str(jwt_keys.private_key), algorithm="RS256"
    )
    client = RequestsClient()

    sensor01_user = User.objects.get(username=sensor01_token_payload["user_name"])
    kws = {"pk": sensor01_user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    response = client.get(
        f"{live_server.url}{user_detail}", headers=get_headers(encoded)
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_token_hidden(live_server, jwt_keys):
    token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
    encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
    client = RequestsClient()
    headers = get_headers(encoded)
    response = client.get(f"{live_server.url}", headers=headers)
    assert response.status_code == 200

    sensor01_user = User.objects.get(username=token_payload["user_name"])
    kws = {"pk": sensor01_user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    client = RequestsClient()
    response = client.get(f"{live_server.url}{user_detail}", headers=headers)
    assert response.status_code == 200
    assert (
        response.json()["auth_token"] == "knox.auth.TokenAuthentication is not enabled"
    )


@pytest.mark.django_db
def test_change_token_role_bad_signature(live_server, jwt_keys):
    """Make sure token modified after it was signed is rejected"""
    token_payload = get_token_payload(authorities=["ROLE_USER"])
    encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
    first_period = encoded.find(".")
    second_period = encoded.find(".", first_period + 1)
    payload = encoded[first_period + 1 : second_period]
    payload_bytes = payload.encode("utf-8")
    # must be multiple of 4 for b64decode
    for i in range(len(payload_bytes) % 4):
        payload_bytes = payload_bytes + b"="
    decoded = base64.b64decode(payload_bytes)
    payload_str = decoded.decode("utf-8")
    payload_data = json.loads(payload_str)
    payload_data["user_name"] = "sensor013"
    payload_data["authorities"] = ["ROLE_MANAGER"]
    payload_data["userDetails"]["authorities"] = [{"authority": "ROLE_MANAGER"}]
    payload_str = json.dumps(payload_data)
    modified_payload = base64.b64encode(payload_str.encode("utf-8"))
    modified_payload = modified_payload.decode("utf-8")
    # remove padding
    if modified_payload.endswith("="):
        last_padded_index = len(modified_payload) - 1
        for i in range(len(modified_payload) - 1, -1, -1):
            if modified_payload[i] != "=":
                last_padded_index = i
                break
        modified_payload = modified_payload[: last_padded_index + 1]
    modified_token = (
        encoded[:first_period]
        + "."
        + modified_payload
        + "."
        + encoded[second_period + 1 :]
    )
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(modified_token))
    assert response.status_code == 403
    assert response.json()["detail"] == "Unable to verify token!"
