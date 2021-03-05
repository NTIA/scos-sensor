import base64
import json
import os
import secrets
import uuid
from datetime import datetime, timedelta

import jwt
import pem
import pytest
from cryptography.x509 import load_pem_x509_certificate
from django import conf
from rest_framework.reverse import reverse
from rest_framework.test import RequestsClient

from authentication.auth import oauth_jwt_authentication_enabled
from authentication.models import User
from sensor import V1

pytestmark = pytest.mark.skipif(
    not oauth_jwt_authentication_enabled,
    reason="OAuth JWT authentication is not enabled!",
)


TEST_JWT_PUBLIC_KEY_FILE = os.path.join(conf.settings.CERTS_DIR, "test/test_pubkey.pem")
TEST_JWT_PRIVATE_KEY_FILE = os.path.join(
    conf.settings.CERTS_DIR, "test/test_private_key.pem"
)
PRIVATE_KEY = None
PUBLIC_KEY = None
jwt_content_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "jwt_content_example.json"
)
with open(jwt_content_file) as token_file:
    TOKEN_CONTENT = json.load(token_file)

with open(TEST_JWT_PRIVATE_KEY_FILE, "rb") as pem_file:
    certs = pem.parse(pem_file.read())

for cert in certs:
    byte_data = cert.as_bytes()
    if type(cert) in [pem.RSAPublicKey, pem.Certificate]:
        x509_cert = load_pem_x509_certificate(byte_data)
        for attribute in x509_cert.subject:
            # check commonName (oid = 2.5.4.3)
            if (
                attribute.oid.dotted_string == "2.5.4.3"
                and attribute.value == "sensor01"
            ):
                PUBLIC_KEY = cert
    elif type(cert) in [pem.RSAPrivateKey, pem.PrivateKey]:
        PRIVATE_KEY = cert
    else:
        raise Exception(f"not checking for type = {type(cert)}")

BAD_PRIVATE_KEY_FILE = os.path.join(
    conf.settings.CERTS_DIR, "test/test_bad_private_key.pem"
)
BAD_PRIVATE_KEY = None
with open(BAD_PRIVATE_KEY_FILE, "rb") as pem_file:
    certs = pem.parse(pem_file.read())
    for cert in certs:
        byte_data = cert.as_bytes()
        if type(cert) in [pem.RSAPrivateKey, pem.PrivateKey]:
            BAD_PRIVATE_KEY = cert
BAD_PUBLIC_KEY_FILE = os.path.join(conf.settings.CERTS_DIR, "test/test_bad_pubkey.pem")

one_min = timedelta(minutes=1)
one_day = timedelta(days=1)


def get_token_payload(authorities=["ROLE_MANAGER"], exp=None, client_id=None, uid=None):
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
    if not uid:
        uid = str(uuid.uuid4())
    token_payload["userDetails"]["uid"] = uid
    token_payload["authorities"] = authorities
    if client_id:
        token_payload["client_id"] = client_id
    return token_payload, uid


def get_headers(uuid, token):
    return {
        "Authorization": f"Bearer {token}",
        "X-Ssl-Client-Dn": f"UID={uuid},CN=Test,OU=Test,O=Test,L=Test,ST=Test,C=Test",
    }


@pytest.mark.django_db
def test_no_token_unauthorized(live_server):
    client = RequestsClient()
    response = client.get(f"{live_server.url}")
    assert response.status_code == 403


@pytest.mark.django_db
def test_token_no_roles_unauthorized(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    token_payload, uid = get_token_payload(authorities=[])
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 403


@pytest.mark.django_db
def test_token_role_manager_accepted(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    token_payload, uid = get_token_payload()
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 200


def test_bad_token_forbidden(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    client = RequestsClient()
    token = (
        secrets.token_urlsafe(28)
        + "."
        + secrets.token_urlsafe(679)
        + "."
        + secrets.token_urlsafe(525)
    )
    response = client.get(f"{live_server.url}", headers=get_headers("test_uid", token))
    print(f"headers: {response.request.headers}")
    assert response.status_code == 403


@pytest.mark.django_db
def test_token_expired_1_day_forbidden(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    current_datetime = datetime.now()
    token_payload, uid = get_token_payload(exp=(current_datetime - one_day).timestamp())
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 403


@pytest.mark.django_db
def test_bad_private_key_forbidden(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    token_payload, uid = get_token_payload()
    encoded = jwt.encode(token_payload, str(BAD_PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 403


@pytest.mark.django_db
def test_bad_public_key_forbidden(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = BAD_PUBLIC_KEY_FILE
    token_payload, uid = get_token_payload()
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 403


@pytest.mark.django_db
def test_token_expired_1_min_forbidden(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    current_datetime = datetime.now()
    token_payload, uid = get_token_payload(exp=(current_datetime - one_min).timestamp())
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 403


@pytest.mark.django_db
def test_token_expires_in_1_min_accepted(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    current_datetime = datetime.now()
    token_payload, uid = get_token_payload(exp=(current_datetime + one_min).timestamp())
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 200


@pytest.mark.django_db
def test_token_role_user_forbidden(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    token_payload, uid = get_token_payload(authorities=["ROLE_USER"])
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 403


@pytest.mark.django_db
def test_token_role_user_required_role_accepted(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    settings.REQUIRED_ROLE = "ROLE_USER"
    token_payload, uid = get_token_payload(authorities=["ROLE_USER"])
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 200


@pytest.mark.django_db
def test_token_multiple_roles_accepted(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    token_payload, uid = get_token_payload(
        authorities=["ROLE_MANAGER", "ROLE_USER", "ROLE_ITS"]
    )
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 200


@pytest.mark.django_db
def test_token_mulitple_roles_forbidden(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    token_payload, uid = get_token_payload(
        authorities=["ROLE_SENSOR", "ROLE_USER", "ROLE_ITS"]
    )
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 403


@pytest.mark.django_db
def test_urls_unauthorized(settings, live_server, user):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    token_payload, uid = get_token_payload(authorities=["ROLE_USER"])
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    headers = get_headers(uid, utf8_bytes)

    capabilities = reverse("capabilities", kwargs=V1)
    response = client.get(f"{live_server.url}{capabilities}", headers=headers,)
    assert response.status_code == 403

    schedule_list = reverse("schedule-list", kwargs=V1)
    response = client.get(f"{live_server.url}{schedule_list}", headers=headers,)
    assert response.status_code == 403

    status = reverse("status", kwargs=V1)
    response = client.get(f"{live_server.url}{status}", headers=headers)
    assert response.status_code == 403

    task_root = reverse("task-root", kwargs=V1)
    response = client.get(f"{live_server.url}{task_root}", headers=headers,)
    assert response.status_code == 403

    task_results_overview = reverse("task-results-overview", kwargs=V1)
    response = client.get(f"{live_server.url}{task_results_overview}", headers=headers,)
    assert response.status_code == 403

    upcoming_tasks = reverse("upcoming-tasks", kwargs=V1)
    response = client.get(f"{live_server.url}{upcoming_tasks}", headers=headers,)
    assert response.status_code == 403

    user_list = reverse("user-list", kwargs=V1)
    response = client.get(f"{live_server.url}{user_list}", headers=headers,)
    assert response.status_code == 403


@pytest.mark.django_db
def test_urls_authorized(settings, live_server, admin_user):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    token_payload, uid = get_token_payload(authorities=["ROLE_MANAGER"])
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    headers = get_headers(uid, utf8_bytes)

    capabilities = reverse("capabilities", kwargs=V1)
    response = client.get(f"{live_server.url}{capabilities}", headers=headers,)
    assert response.status_code == 200

    schedule_list = reverse("schedule-list", kwargs=V1)
    response = client.get(f"{live_server.url}{schedule_list}", headers=headers,)
    assert response.status_code == 200

    status = reverse("status", kwargs=V1)
    response = client.get(f"{live_server.url}{status}", headers=headers)
    assert response.status_code == 200

    task_root = reverse("task-root", kwargs=V1)
    response = client.get(f"{live_server.url}{task_root}", headers=headers,)
    assert response.status_code == 200

    task_results_overview = reverse("task-results-overview", kwargs=V1)
    response = client.get(f"{live_server.url}{task_results_overview}", headers=headers,)
    assert response.status_code == 200

    upcoming_tasks = reverse("upcoming-tasks", kwargs=V1)
    response = client.get(f"{live_server.url}{upcoming_tasks}", headers=headers,)
    assert response.status_code == 200

    user_list = reverse("user-list", kwargs=V1)
    response = client.get(f"{live_server.url}{user_list}", headers=headers,)
    assert response.status_code == 200


@pytest.mark.django_db
def test_user_cannot_view_user_detail(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    sensor01_token_payload, sensor01_uid = get_token_payload(
        authorities=["ROLE_MANAGER"]
    )
    encoded = jwt.encode(sensor01_token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(
        f"{live_server.url}", headers=get_headers(sensor01_uid, utf8_bytes)
    )
    assert response.status_code == 200

    sensor02_token_payload, sensor02_uid = get_token_payload(authorities=["ROLE_USER"])
    sensor02_token_payload["user_name"] = "sensor02"
    encoded = jwt.encode(sensor02_token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()

    sensor01_user = User.objects.get(username=sensor01_token_payload["user_name"])
    kws = {"pk": sensor01_user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    response = client.get(
        f"{live_server.url}{user_detail}", headers=get_headers(sensor02_uid, utf8_bytes)
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_user_cannot_view_user_detail_role_change(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    sensor01_token_payload, uid = get_token_payload(authorities=["ROLE_MANAGER"])
    encoded = jwt.encode(sensor01_token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 200

    token_payload, uid = get_token_payload(authorities=["ROLE_USER"])
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()

    sensor01_user = User.objects.get(username=sensor01_token_payload["user_name"])
    kws = {"pk": sensor01_user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    response = client.get(
        f"{live_server.url}{user_detail}", headers=get_headers(uid, utf8_bytes),
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_view_user_detail(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    token_payload, uid = get_token_payload(authorities=["ROLE_MANAGER"])
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    headers = get_headers(uid, utf8_bytes)
    response = client.get(f"{live_server.url}", headers=headers)
    assert response.status_code == 200

    sensor01_user = User.objects.get(username=token_payload["user_name"])
    kws = {"pk": sensor01_user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    response = client.get(f"{live_server.url}{user_detail}", headers=headers,)
    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_can_view_other_user_detail(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    sensor01_token_payload, sensor01_uid = get_token_payload(
        authorities=["ROLE_MANAGER"]
    )
    encoded = jwt.encode(sensor01_token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(
        f"{live_server.url}", headers=get_headers(sensor01_uid, utf8_bytes)
    )
    assert response.status_code == 200

    sensor02_token_payload, sensor02_uid = get_token_payload(
        authorities=["ROLE_MANAGER"]
    )
    sensor02_token_payload["user_name"] = "sensor02"
    encoded = jwt.encode(sensor02_token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()

    sensor01_user = User.objects.get(username=sensor01_token_payload["user_name"])
    kws = {"pk": sensor01_user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    response = client.get(
        f"{live_server.url}{user_detail}",
        headers=get_headers(sensor02_uid, utf8_bytes),
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_token_hidden(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    token_payload, uid = get_token_payload(authorities=["ROLE_MANAGER"])
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    headers = get_headers(uid, utf8_bytes)
    response = client.get(f"{live_server.url}", headers=headers)
    assert response.status_code == 200

    sensor01_user = User.objects.get(username=token_payload["user_name"])
    kws = {"pk": sensor01_user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    client = RequestsClient()
    response = client.get(f"{live_server.url}{user_detail}", headers=headers,)
    assert response.status_code == 200
    assert (
        response.json()["auth_token"]
        == "rest_framework.authentication.TokenAuthentication is not enabled"
    )


@pytest.mark.django_db
def test_change_token_role_bad_signature(settings, live_server):
    """Make sure token modified after it was signed is rejected"""
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    token_payload, uid = get_token_payload(authorities=["ROLE_USER"])
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    first_period = utf8_bytes.find(".")
    second_period = utf8_bytes.find(".", first_period + 1)
    payload = utf8_bytes[first_period + 1 : second_period]
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
    encoded = base64.b64encode(payload_str.encode("utf-8"))
    modified_payload = encoded.decode("utf-8")
    # remove padding
    if modified_payload.endswith("="):
        last_padded_index = len(modified_payload) - 1
        for i in range(len(modified_payload) - 1, -1, -1):
            if modified_payload[i] != "=":
                last_padded_index = i
                break
        modified_payload = modified_payload[: last_padded_index + 1]
    modified_token = (
        utf8_bytes[:first_period]
        + "."
        + modified_payload
        + "."
        + utf8_bytes[second_period + 1 :]
    )
    client = RequestsClient()
    response = client.get(
        f"{live_server.url}", headers=get_headers(uid, modified_token)
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_token_bad_client_id_forbidden(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    token_payload, uid = get_token_payload(client_id="bad_client_id")
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 403


@pytest.mark.django_db
def test_no_client_id_forbidden(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    token_payload, uid = get_token_payload(client_id="bad_client_id")
    del token_payload["client_id"]
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 403


@pytest.mark.django_db
def test_client_id_none_forbidden(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    token_payload, uid = get_token_payload(client_id="bad_client_id")
    token_payload["client_id"] = None
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 403


@pytest.mark.django_db
def test_client_id_empty_forbidden(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    token_payload, uid = get_token_payload(client_id="bad_client_id")
    token_payload["client_id"] = ""
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 403


@pytest.mark.django_db
def test_jwt_uid_missing(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    token_payload, uid = get_token_payload()
    token_payload["userDetails"].pop("uid")
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 403

    token_payload, uid = get_token_payload()
    token_payload["userDetails"]["uid"] = None
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 403

    token_payload, uid = get_token_payload()
    token_payload["userDetails"]["uid"] = ""
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 403


def test_header_uid_missing(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    token_payload, _ = get_token_payload()
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(
        f"{live_server.url}", headers={"Authorization": f"Bearer {utf8_bytes}",}
    )
    assert response.status_code == 403

    response = client.get(
        f"{live_server.url}",
        headers={"Authorization": f"Bearer {utf8_bytes}", "X-Ssl-Client-Dn": None},
    )
    assert response.status_code == 403

    response = client.get(
        f"{live_server.url}",
        headers={"Authorization": f"Bearer {utf8_bytes}", "X-Ssl-Client-Dn": ""},
    )
    assert response.status_code == 403


def test_header_jwt_uid_mismatch(settings, live_server):
    settings.PATH_TO_JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY_FILE
    token_payload, uid = get_token_payload()
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(
        f"{live_server.url}", headers=get_headers("test_uid", utf8_bytes)
    )
    assert response.status_code == 403

    token_payload["userDetails"]["uid"] = "test_uid"
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm="RS256")
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_headers(uid, utf8_bytes))
    assert response.status_code == 403
