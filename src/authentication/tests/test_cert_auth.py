import base64
import json
import os
import secrets
from datetime import datetime, timedelta
from tempfile import NamedTemporaryFile

import pytest
from rest_framework.reverse import reverse
from rest_framework.test import RequestsClient

from authentication.auth import certificate_authentication_enabled
from authentication.models import User
from sensor import V1
from sensor.tests.utils import get_requests_ssl_dn_header

pytestmark = pytest.mark.skipif(
    not certificate_authentication_enabled,
    reason="Certificate authentication is not enabled!",
)




one_min = timedelta(minutes=1)
one_day = timedelta(days=1)





@pytest.mark.django_db
def test_no_client_cert_unauthorized(live_server):
    client = RequestsClient()
    response = client.get(f"{live_server.url}")
    assert response.status_code == 403



@pytest.mark.django_db
def test_client_cert_accepted(live_server, admin_user):
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_requests_ssl_dn_header("admin"))
    assert response.status_code == 200


def test_bad_client_cert_forbidden(live_server, admin_user):
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_requests_ssl_dn_header("user"))
    assert response.status_code == 403
    assert "No matching username found!" in response.json()["detail"]


# @pytest.mark.django_db
# def test_certificate_expired_1_day_forbidden(live_server):
#     current_datetime = datetime.now()
#     token_payload = get_token_payload(exp=(current_datetime - one_day).timestamp())
#     encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
#     client = RequestsClient()
#     response = client.get(f"{live_server.url}", headers=get_headers(encoded))
#     assert response.status_code == 403
#     assert response.json()["detail"] == "Token is expired!"


# @pytest.mark.django_db
# def test_bad_private_key_forbidden(live_server):
#     token_payload = get_token_payload()
#     encoded = jwt.encode(
#         token_payload, str(BAD_PRIVATE_KEY.decode("utf-8")), algorithm="RS256"
#     )
#     client = RequestsClient()
#     response = client.get(f"{live_server.url}", headers=get_headers(encoded))
#     assert response.status_code == 403
#     assert response.json()["detail"] == "Unable to verify token!"


# @pytest.mark.django_db
# def test_bad_public_key_forbidden(settings, live_server):
#     with NamedTemporaryFile() as jwt_public_key_file:
#         jwt_public_key_file.write(BAD_PUBLIC_KEY)
#         jwt_public_key_file.flush()
#         settings.PATH_TO_JWT_PUBLIC_KEY = jwt_public_key_file.name
#         token_payload = get_token_payload()
#         encoded = jwt.encode(
#             token_payload, str(jwt_keys.private_key), algorithm="RS256"
#         )
#         client = RequestsClient()
#         response = client.get(f"{live_server.url}", headers=get_headers(encoded))
#         assert response.status_code == 403
#         assert response.json()["detail"] == "Unable to verify token!"


# @pytest.mark.django_db
# def test_certificate_expired_1_min_forbidden(live_server):
#     current_datetime = datetime.now()
#     token_payload = get_token_payload(exp=(current_datetime - one_min).timestamp())
#     encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
#     client = RequestsClient()
#     response = client.get(f"{live_server.url}", headers=get_headers(encoded))
#     assert response.status_code == 403
#     assert response.json()["detail"] == "Token is expired!"


# @pytest.mark.django_db
# def test_certificate_expires_in_1_min_accepted(live_server):
#     current_datetime = datetime.now()
#     token_payload = get_token_payload(exp=(current_datetime + one_min).timestamp())
#     encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
#     client = RequestsClient()
#     response = client.get(f"{live_server.url}", headers=get_headers(encoded))
#     assert response.status_code == 200


# @pytest.mark.django_db
# def test_urls_unauthorized(live_server):
#     token_payload = get_token_payload(authorities=["ROLE_USER"])
#     encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
#     client = RequestsClient()
#     headers = get_headers(encoded)

#     capabilities = reverse("capabilities", kwargs=V1)
#     response = client.get(f"{live_server.url}{capabilities}", headers=headers)
#     assert response.status_code == 403

#     schedule_list = reverse("schedule-list", kwargs=V1)
#     response = client.get(f"{live_server.url}{schedule_list}", headers=headers)
#     assert response.status_code == 403

#     status = reverse("status", kwargs=V1)
#     response = client.get(f"{live_server.url}{status}", headers=headers)
#     assert response.status_code == 403

#     task_root = reverse("task-root", kwargs=V1)
#     response = client.get(f"{live_server.url}{task_root}", headers=headers)
#     assert response.status_code == 403

#     task_results_overview = reverse("task-results-overview", kwargs=V1)
#     response = client.get(f"{live_server.url}{task_results_overview}", headers=headers)
#     assert response.status_code == 403

#     upcoming_tasks = reverse("upcoming-tasks", kwargs=V1)
#     response = client.get(f"{live_server.url}{upcoming_tasks}", headers=headers)
#     assert response.status_code == 403

#     user_list = reverse("user-list", kwargs=V1)
#     response = client.get(f"{live_server.url}{user_list}", headers=headers)
#     assert response.status_code == 403


# @pytest.mark.django_db
# def test_urls_authorized(live_server):
#     token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
#     encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
#     client = RequestsClient()
#     headers = get_headers(encoded)

#     capabilities = reverse("capabilities", kwargs=V1)
#     response = client.get(f"{live_server.url}{capabilities}", headers=headers)
#     assert response.status_code == 200

#     schedule_list = reverse("schedule-list", kwargs=V1)
#     response = client.get(f"{live_server.url}{schedule_list}", headers=headers)
#     assert response.status_code == 200

#     status = reverse("status", kwargs=V1)
#     response = client.get(f"{live_server.url}{status}", headers=headers)
#     assert response.status_code == 200

#     task_root = reverse("task-root", kwargs=V1)
#     response = client.get(f"{live_server.url}{task_root}", headers=headers)
#     assert response.status_code == 200

#     task_results_overview = reverse("task-results-overview", kwargs=V1)
#     response = client.get(f"{live_server.url}{task_results_overview}", headers=headers)
#     assert response.status_code == 200

#     upcoming_tasks = reverse("upcoming-tasks", kwargs=V1)
#     response = client.get(f"{live_server.url}{upcoming_tasks}", headers=headers)
#     assert response.status_code == 200

#     user_list = reverse("user-list", kwargs=V1)
#     response = client.get(f"{live_server.url}{user_list}", headers=headers)
#     assert response.status_code == 200


# @pytest.mark.django_db
# def test_user_cannot_view_user_detail(live_server):
#     sensor01_token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
#     encoded = jwt.encode(
#         sensor01_token_payload, str(jwt_keys.private_key), algorithm="RS256"
#     )
#     client = RequestsClient()
#     response = client.get(f"{live_server.url}", headers=get_headers(encoded))
#     assert response.status_code == 200

#     sensor02_token_payload = get_token_payload(authorities=["ROLE_USER"])
#     sensor02_token_payload["user_name"] = "sensor02"
#     encoded = jwt.encode(
#         sensor02_token_payload, str(jwt_keys.private_key), algorithm="RS256"
#     )
#     client = RequestsClient()

#     sensor01_user = User.objects.get(username=sensor01_token_payload["user_name"])
#     kws = {"pk": sensor01_user.pk}
#     kws.update(V1)
#     user_detail = reverse("user-detail", kwargs=kws)
#     response = client.get(
#         f"{live_server.url}{user_detail}", headers=get_headers(encoded)
#     )
#     assert response.status_code == 403


# @pytest.mark.django_db
# def test_user_cannot_view_user_detail_role_change(live_server):
#     sensor01_token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
#     encoded = jwt.encode(
#         sensor01_token_payload, str(jwt_keys.private_key), algorithm="RS256"
#     )
#     client = RequestsClient()
#     response = client.get(f"{live_server.url}", headers=get_headers(encoded))
#     assert response.status_code == 200

#     token_payload = get_token_payload(authorities=["ROLE_USER"])
#     encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
#     client = RequestsClient()

#     sensor01_user = User.objects.get(username=sensor01_token_payload["user_name"])
#     kws = {"pk": sensor01_user.pk}
#     kws.update(V1)
#     user_detail = reverse("user-detail", kwargs=kws)
#     response = client.get(
#         f"{live_server.url}{user_detail}", headers=get_headers(encoded)
#     )
#     assert response.status_code == 403


# @pytest.mark.django_db
# def test_admin_can_view_user_detail(live_server):
#     token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
#     encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
#     client = RequestsClient()
#     headers = get_headers(encoded)
#     response = client.get(f"{live_server.url}", headers=headers)
#     assert response.status_code == 200

#     sensor01_user = User.objects.get(username=token_payload["user_name"])
#     kws = {"pk": sensor01_user.pk}
#     kws.update(V1)
#     user_detail = reverse("user-detail", kwargs=kws)
#     response = client.get(f"{live_server.url}{user_detail}", headers=headers)
#     assert response.status_code == 200


# @pytest.mark.django_db
# def test_admin_can_view_other_user_detail(live_server):
#     sensor01_token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
#     encoded = jwt.encode(
#         sensor01_token_payload, str(jwt_keys.private_key), algorithm="RS256"
#     )
#     client = RequestsClient()
#     response = client.get(f"{live_server.url}", headers=get_headers(encoded))
#     assert response.status_code == 200

#     sensor02_token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
#     sensor02_token_payload["user_name"] = "sensor02"
#     encoded = jwt.encode(
#         sensor02_token_payload, str(jwt_keys.private_key), algorithm="RS256"
#     )
#     client = RequestsClient()

#     sensor01_user = User.objects.get(username=sensor01_token_payload["user_name"])
#     kws = {"pk": sensor01_user.pk}
#     kws.update(V1)
#     user_detail = reverse("user-detail", kwargs=kws)
#     response = client.get(
#         f"{live_server.url}{user_detail}", headers=get_headers(encoded)
#     )
#     assert response.status_code == 200


# @pytest.mark.django_db
# def test_token_hidden(live_server):
#     token_payload = get_token_payload(authorities=["ROLE_MANAGER"])
#     encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
#     client = RequestsClient()
#     headers = get_headers(encoded)
#     response = client.get(f"{live_server.url}", headers=headers)
#     assert response.status_code == 200

#     sensor01_user = User.objects.get(username=token_payload["user_name"])
#     kws = {"pk": sensor01_user.pk}
#     kws.update(V1)
#     user_detail = reverse("user-detail", kwargs=kws)
#     client = RequestsClient()
#     response = client.get(f"{live_server.url}{user_detail}", headers=headers)
#     assert response.status_code == 200
#     assert (
#         response.json()["auth_token"]
#         == "rest_framework.authentication.TokenAuthentication is not enabled"
#     )


# @pytest.mark.django_db
# def test_change_token_role_bad_signature(live_server):
#     """Make sure token modified after it was signed is rejected"""
#     token_payload = get_token_payload(authorities=["ROLE_USER"])
#     encoded = jwt.encode(token_payload, str(jwt_keys.private_key), algorithm="RS256")
#     first_period = encoded.find(".")
#     second_period = encoded.find(".", first_period + 1)
#     payload = encoded[first_period + 1 : second_period]
#     payload_bytes = payload.encode("utf-8")
#     # must be multiple of 4 for b64decode
#     for i in range(len(payload_bytes) % 4):
#         payload_bytes = payload_bytes + b"="
#     decoded = base64.b64decode(payload_bytes)
#     payload_str = decoded.decode("utf-8")
#     payload_data = json.loads(payload_str)
#     payload_data["user_name"] = "sensor013"
#     payload_data["authorities"] = ["ROLE_MANAGER"]
#     payload_data["userDetails"]["authorities"] = [{"authority": "ROLE_MANAGER"}]
#     payload_str = json.dumps(payload_data)
#     modified_payload = base64.b64encode(payload_str.encode("utf-8"))
#     modified_payload = modified_payload.decode("utf-8")
#     # remove padding
#     if modified_payload.endswith("="):
#         last_padded_index = len(modified_payload) - 1
#         for i in range(len(modified_payload) - 1, -1, -1):
#             if modified_payload[i] != "=":
#                 last_padded_index = i
#                 break
#         modified_payload = modified_payload[: last_padded_index + 1]
#     modified_token = (
#         encoded[:first_period]
#         + "."
#         + modified_payload
#         + "."
#         + encoded[second_period + 1 :]
#     )
#     client = RequestsClient()
#     response = client.get(f"{live_server.url}", headers=get_headers(modified_token))
#     assert response.status_code == 403
#     assert response.json()["detail"] == "Unable to verify token!"
