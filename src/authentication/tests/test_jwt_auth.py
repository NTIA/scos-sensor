import pytest
from rest_framework.reverse import reverse
from rest_framework.test import RequestsClient
import pem
from cryptography.x509 import load_pem_x509_certificate
import json
from datetime import datetime, timedelta
import jwt
import os
from authentication.models import User
import secrets

from sensor import V1


TEST_JWT_PUBLIC_KEY_FILE = "authentication/tests/certs/sensor01_pubkey.pem"
TEST_JWT_PRIVATE_KEY_FILE = "authentication/tests/certs/sensor01_private.pem"
PRIVATE_KEY = None
PUBLIC_KEY = None
jwt_content_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jwt_content_example.json")
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
            if attribute.oid.dotted_string == "2.5.4.3" and attribute.value == "sensor01":
                PUBLIC_KEY = cert
    elif type(cert) in [pem.RSAPrivateKey, pem.PrivateKey]:
        PRIVATE_KEY = cert
    else:
        raise Exception(f"not checking for type = {type(cert)}")

BAD_PRIVATE_KEY = None
with open("authentication/tests/certs/test_bad_private_key.pem", "rb") as pem_file:
    certs = pem.parse(pem_file.read())
    for cert in certs:
        byte_data = cert.as_bytes()
        if type(cert) in [pem.RSAPrivateKey, pem.PrivateKey]:
            BAD_PRIVATE_KEY = cert


one_min = timedelta(minutes=1)
one_day = timedelta(days=1)

def get_token_payload(authorities=["ROLE_MANAGER"], exp=None):
    token_payload = TOKEN_CONTENT.copy()
    current_datetime = datetime.now()
    if not exp:
        token_payload["exp"] = (current_datetime + one_day).timestamp()
    else:
        token_payload["exp"] = exp
    token_payload["userDetails"]["lastlogin"] = (current_datetime - one_day).timestamp()
    token_payload["userDetails"]["authorities"] = []
    for authority in authorities:
        token_payload["userDetails"]["authorities"].append({"authority":  authority})
    token_payload["userDetails"]["enabled"] = True
    token_payload["authorities"] = authorities
    return token_payload

@pytest.mark.django_db
def test_no_token_unauthorized(live_server):
    client = RequestsClient()
    response = client.get(f"{live_server.url}")
    assert response.status_code == 403

@pytest.mark.django_db
def test_token_no_roles_unauthorized(settings, live_server):
    settings.JWT_PUBLIC_KEY_FILE = TEST_JWT_PUBLIC_KEY_FILE
    token_payload = get_token_payload(authorities=[])
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 403

@pytest.mark.django_db
def test_token_role_manager_accepted(settings, live_server):
    settings.JWT_PUBLIC_KEY_FILE = TEST_JWT_PUBLIC_KEY_FILE
    token_payload = get_token_payload()
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 200

def test_bad_token_forbidden(settings, live_server):
    settings.JWT_PUBLIC_KEY_FILE = TEST_JWT_PUBLIC_KEY_FILE
    client = RequestsClient()
    token = secrets.token_urlsafe(28)  + "." + secrets.token_urlsafe(679) + "." + secrets.token_urlsafe(525)
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Bearer {token}"})
    print(f"headers: {response.request.headers}")
    assert response.status_code == 403

@pytest.mark.django_db
def test_token_expired_1_day_forbidden(settings, live_server):
    settings.JWT_PUBLIC_KEY_FILE = TEST_JWT_PUBLIC_KEY_FILE
    current_datetime = datetime.now()
    token_payload = get_token_payload(exp=(current_datetime - one_day).timestamp())
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 403

@pytest.mark.django_db
def test_bad_private_key_forbidden(settings, live_server):
    settings.JWT_PUBLIC_KEY_FILE = TEST_JWT_PUBLIC_KEY_FILE
    token_payload = get_token_payload()
    encoded = jwt.encode(token_payload, str(BAD_PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 403

@pytest.mark.django_db
def test_bad_public_key_forbidden(settings, live_server):
    settings.JWT_PUBLIC_KEY_FILE = "authentication/tests/certs/test_bad_pubkey.pem"
    token_payload = get_token_payload()
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 403

@pytest.mark.django_db
def test_token_expired_1_min_forbidden(settings, live_server):
    settings.JWT_PUBLIC_KEY_FILE = TEST_JWT_PUBLIC_KEY_FILE
    current_datetime = datetime.now()
    token_payload = get_token_payload(exp=(current_datetime-one_min).timestamp())
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 403

@pytest.mark.django_db
def test_token_expires_in_1_min_accepted(settings, live_server):
    settings.JWT_PUBLIC_KEY_FILE = TEST_JWT_PUBLIC_KEY_FILE
    current_datetime = datetime.now()
    token_payload = get_token_payload(exp=(current_datetime + one_min).timestamp())
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 200

@pytest.mark.django_db
def test_token_role_user_forbidden(settings, live_server):
    settings.JWT_PUBLIC_KEY_FILE = TEST_JWT_PUBLIC_KEY_FILE
    token_payload = get_token_payload(authorities=["ROLE_USER"])
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 403

@pytest.mark.django_db
def test_token_role_user_required_role_accepted(settings, live_server):
    settings.JWT_PUBLIC_KEY_FILE = TEST_JWT_PUBLIC_KEY_FILE
    settings.REQUIRED_ROLE = "ROLE_USER"
    token_payload = get_token_payload(authorities=["ROLE_USER"])
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 200

@pytest.mark.django_db
def test_token_mulitple_roles_accepted(settings, live_server):
    settings.JWT_PUBLIC_KEY_FILE = TEST_JWT_PUBLIC_KEY_FILE
    token_payload = get_token_payload(authorities=["ROLE_MANAGER", "ROLE_USER", "ROLE_ITS"])
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 200

@pytest.mark.django_db
def test_token_mulitple_roles_forbidden(settings, live_server):
    settings.JWT_PUBLIC_KEY_FILE = TEST_JWT_PUBLIC_KEY_FILE
    token_payload = get_token_payload(authorities=["ROLE_SENSOR", "ROLE_USER", "ROLE_ITS"])
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 403

@pytest.mark.django_db
def test_urls_unauthorized(settings, live_server, user):
    settings.JWT_PUBLIC_KEY_FILE = TEST_JWT_PUBLIC_KEY_FILE
    token_payload = get_token_payload(authorities=["ROLE_USER"])
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()

    capabilities = reverse("capabilities", kwargs=V1)
    response = client.get(f"{live_server.url}{capabilities}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 403

    schedule_list = reverse("schedule-list", kwargs=V1)
    response = client.get(f"{live_server.url}{schedule_list}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 403

    status = reverse("status", kwargs=V1)
    response = client.get(f"{live_server.url}{status}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 403

    task_root = reverse("task-root", kwargs=V1)
    response = client.get(f"{live_server.url}{task_root}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 403

    task_results_overview = reverse("task-results-overview", kwargs=V1)
    response = client.get(f"{live_server.url}{task_results_overview}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 403

    upcoming_tasks = reverse("upcoming-tasks", kwargs=V1)
    response = client.get(f"{live_server.url}{upcoming_tasks}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 403

    user_list = reverse("user-list", kwargs=V1)
    response = client.get(f"{live_server.url}{user_list}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 403

@pytest.mark.django_db
def test_urls_authorized(settings, live_server, admin_user):
    settings.JWT_PUBLIC_KEY_FILE = TEST_JWT_PUBLIC_KEY_FILE
    token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()

    capabilities = reverse("capabilities", kwargs=V1)
    response = client.get(f"{live_server.url}{capabilities}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 200

    schedule_list = reverse("schedule-list", kwargs=V1)
    response = client.get(f"{live_server.url}{schedule_list}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 200

    status = reverse("status", kwargs=V1)
    response = client.get(f"{live_server.url}{status}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 200

    task_root = reverse("task-root", kwargs=V1)
    response = client.get(f"{live_server.url}{task_root}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 200

    task_results_overview = reverse("task-results-overview", kwargs=V1)
    response = client.get(f"{live_server.url}{task_results_overview}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 200

    upcoming_tasks = reverse("upcoming-tasks", kwargs=V1)
    response = client.get(f"{live_server.url}{upcoming_tasks}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 200

    user_list = reverse("user-list", kwargs=V1)
    response = client.get(f"{live_server.url}{user_list}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 200
    
@pytest.mark.django_db
def test_user_cannot_view_user_detail(settings, live_server):
    settings.JWT_PUBLIC_KEY_FILE = TEST_JWT_PUBLIC_KEY_FILE
    sensor01_token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
    encoded = jwt.encode(sensor01_token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    # authenticating with "ROLE_MANAGER" creates user if does not already exist
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 200

    sensor02_token_payload = get_token_payload(authorities=["ROLE_USER"])
    sensor02_token_payload["user_name"] = "sensor02.sms.internal"
    encoded = jwt.encode(sensor02_token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()

    sensor01_user = User.objects.get(username=sensor01_token_payload["user_name"])
    kws = {"pk": sensor01_user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    response = client.get(f"{live_server.url}{user_detail}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 403

@pytest.mark.django_db
def test_user_cannot_view_user_detail_role_change(settings, live_server):
    settings.JWT_PUBLIC_KEY_FILE = TEST_JWT_PUBLIC_KEY_FILE
    sensor01_token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
    encoded = jwt.encode(sensor01_token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    # authenticating with "ROLE_MANAGER" creates user if does not already exist
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 200

    token_payload = get_token_payload(authorities=["ROLE_USER"])
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()

    sensor01_user = User.objects.get(username=sensor01_token_payload["user_name"])
    kws = {"pk": sensor01_user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    response = client.get(f"{live_server.url}{user_detail}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 403

@pytest.mark.django_db
def test_admin_can_view_user_detail(settings, live_server):
    settings.JWT_PUBLIC_KEY_FILE = TEST_JWT_PUBLIC_KEY_FILE
    token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    # authenticating with "ROLE_MANAGER" creates user if does not already exist
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 200

    sensor01_user = User.objects.get(username=token_payload["user_name"])
    kws = {"pk": sensor01_user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    response = client.get(f"{live_server.url}{user_detail}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 200

@pytest.mark.django_db
def test_admin_can_view_other_user_detail(settings, live_server):
    settings.JWT_PUBLIC_KEY_FILE = TEST_JWT_PUBLIC_KEY_FILE
    sensor01_token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
    encoded = jwt.encode(sensor01_token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    # authenticating with "ROLE_MANAGER" creates user if does not already exist
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 200

    sensor02_token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
    sensor02_token_payload["user_name"] = "sensor02.sms.internal"
    encoded = jwt.encode(sensor02_token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()

    sensor01_user = User.objects.get(username=sensor01_token_payload["user_name"])
    kws = {"pk": sensor01_user.pk}
    kws.update(V1)
    print(f"kws = {kws}")
    user_detail = reverse("user-detail", kwargs=kws)
    response = client.get(f"{live_server.url}{user_detail}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 200

@pytest.mark.django_db
def test_token_hidden(settings, live_server):
    settings.JWT_PUBLIC_KEY_FILE = TEST_JWT_PUBLIC_KEY_FILE
    token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
    encoded = jwt.encode(token_payload, str(PRIVATE_KEY), algorithm='RS256')
    utf8_bytes = encoded.decode("utf-8")
    client = RequestsClient()
    # authenticating with "ROLE_MANAGER" creates user if does not already exist
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 200

    sensor01_user = User.objects.get(username=token_payload["user_name"])
    kws = {"pk": sensor01_user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    client = RequestsClient()
    response = client.get(f"{live_server.url}{user_detail}", headers={"Authorization": f"Bearer {utf8_bytes}"})
    assert response.status_code == 200
    print(f"user detail response = {response.json()}")
    assert response.json()["auth_token"] == "rest_framework.authentication.TokenAuthentication is not enabled"