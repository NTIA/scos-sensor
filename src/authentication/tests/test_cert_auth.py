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


@pytest.mark.django_db
def test_no_client_cert_unauthorized_no_dn(live_server):
    client = RequestsClient()
    response = client.get(f"{live_server.url}")
    assert response.status_code == 403

    capabilities = reverse("capabilities", kwargs=V1)
    response = client.get(f"{live_server.url}{capabilities}")
    assert response.status_code == 403

    schedule_list = reverse("schedule-list", kwargs=V1)
    response = client.get(f"{live_server.url}{schedule_list}")
    assert response.status_code == 403

    status = reverse("status", kwargs=V1)
    response = client.get(f"{live_server.url}{status}")
    assert response.status_code == 403

    task_root = reverse("task-root", kwargs=V1)
    response = client.get(f"{live_server.url}{task_root}")
    assert response.status_code == 403

    task_results_overview = reverse("task-results-overview", kwargs=V1)
    response = client.get(f"{live_server.url}{task_results_overview}")
    assert response.status_code == 403

    upcoming_tasks = reverse("upcoming-tasks", kwargs=V1)
    response = client.get(f"{live_server.url}{upcoming_tasks}")
    assert response.status_code == 403

    user_list = reverse("user-list", kwargs=V1)
    response = client.get(f"{live_server.url}{user_list}")
    assert response.status_code == 403


@pytest.mark.django_db
def test_client_cert_accepted(live_server, admin_user):
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_requests_ssl_dn_header("admin"))
    assert response.status_code == 200


def test_mismatching_user_forbidden(live_server, admin_user):
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_requests_ssl_dn_header("user"))
    assert response.status_code == 403
    assert "No matching username found!" in response.json()["detail"]


@pytest.mark.django_db
def test_urls_unauthorized_not_superuser(live_server, user):
    client = RequestsClient()
    headers = get_requests_ssl_dn_header("user")

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
def test_urls_authorized(live_server, admin_user):
    client = RequestsClient()
    headers = get_requests_ssl_dn_header("admin")

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
def test_token_hidden(live_server, admin_user):
    client = RequestsClient()
    headers = get_requests_ssl_dn_header("admin")
    response = client.get(f"{live_server.url}", headers=headers)
    assert response.status_code == 200

    sensor01_user = User.objects.get(username=admin_user.username)
    kws = {"pk": sensor01_user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    client = RequestsClient()
    response = client.get(f"{live_server.url}{user_detail}", headers=headers)
    assert response.status_code == 200
    assert (
        response.json()["auth_token"]
        == "rest_framework.authentication.TokenAuthentication is not enabled"
    )


@pytest.mark.django_db
def test_empty_common_name_unauthorized(live_server, admin_user):
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers=get_requests_ssl_dn_header(""))
    assert response.status_code == 403


@pytest.mark.django_db
def test_invalid_dn_unauthorized(live_server, admin_user):
    client = RequestsClient()
    headers = {
        "X-Ssl-Client-Dn": f"C=TC,ST=test_state,L=test_locality,O=test_org,OU=test_ou",
    }
    response = client.get(f"{live_server.url}", headers=headers)
    assert response.status_code == 403


@pytest.mark.django_db
def test_empty_dn_unauthorized(live_server, admin_user):
    client = RequestsClient()
    headers = {
        "X-Ssl-Client-Dn": "",
    }
    response = client.get(f"{live_server.url}", headers=headers)
    assert response.status_code == 403