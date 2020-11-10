from rest_framework.reverse import reverse
from rest_framework.test import RequestsClient
import pytest
import secrets
from authentication.auth import token_auth_enabled
from sensor import V1

pytestmark = pytest.mark.skipif(not token_auth_enabled, reason="Token authentication is not enabled!")

def test_no_token_unauthorized(settings, live_server):
    client = RequestsClient()
    response = client.get(f"{live_server.url}")
    assert response.status_code == 401

def test_token_user_unauthorized(settings, live_server, user):
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Token {user.auth_token.key}"})
    print(f"headers: {response.request.headers}")
    assert response.status_code == 403

def test_token_admin_accepted(settings, live_server, admin_user):
    client = RequestsClient()
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Token {admin_user.auth_token.key}"})
    print(f"headers: {response.request.headers}")
    assert response.status_code == 200

def test_bad_token_forbidden(settings, live_server):
    client = RequestsClient()
    token = secrets.token_hex(20)
    response = client.get(f"{live_server.url}", headers={"Authorization": f"Token {token}"})
    print(f"headers: {response.request.headers}")
    assert response.status_code == 401

def test_urls_unauthorized(live_server, user):
    client = RequestsClient()

    capabilities = reverse("capabilities", kwargs=V1)
    response = client.get(f"{live_server.url}{capabilities}", headers={"Authorization": f"Token {user.auth_token.key}"})
    assert response.status_code == 403

    schedule_list = reverse("schedule-list", kwargs=V1)
    response = client.get(f"{live_server.url}{schedule_list}", headers={"Authorization": f"Token {user.auth_token.key}"})
    assert response.status_code == 403

    status = reverse("status", kwargs=V1)
    response = client.get(f"{live_server.url}{status}", headers={"Authorization": f"Token {user.auth_token.key}"})
    assert response.status_code == 403

    task_root = reverse("task-root", kwargs=V1)
    response = client.get(f"{live_server.url}{task_root}", headers={"Authorization": f"Token {user.auth_token.key}"})
    assert response.status_code == 403

    task_results_overview = reverse("task-results-overview", kwargs=V1)
    response = client.get(f"{live_server.url}{task_results_overview}", headers={"Authorization": f"Token {user.auth_token.key}"})
    assert response.status_code == 403

    upcoming_tasks = reverse("upcoming-tasks", kwargs=V1)
    response = client.get(f"{live_server.url}{upcoming_tasks}", headers={"Authorization": f"Token {user.auth_token.key}"})
    assert response.status_code == 403

    user_list = reverse("user-list", kwargs=V1)
    response = client.get(f"{live_server.url}{user_list}", headers={"Authorization": f"Token {user.auth_token.key}"})
    assert response.status_code == 403
    
def test_urls_authorized(live_server, admin_user):
    client = RequestsClient()

    capabilities = reverse("capabilities", kwargs=V1)
    response = client.get(f"{live_server.url}{capabilities}", headers={"Authorization": f"Token {admin_user.auth_token.key}"})
    assert response.status_code == 200

    schedule_list = reverse("schedule-list", kwargs=V1)
    response = client.get(f"{live_server.url}{schedule_list}", headers={"Authorization": f"Token {admin_user.auth_token.key}"})
    assert response.status_code == 200

    status = reverse("status", kwargs=V1)
    response = client.get(f"{live_server.url}{status}", headers={"Authorization": f"Token {admin_user.auth_token.key}"})
    assert response.status_code == 200

    task_root = reverse("task-root", kwargs=V1)
    response = client.get(f"{live_server.url}{task_root}", headers={"Authorization": f"Token {admin_user.auth_token.key}"})
    assert response.status_code == 200

    task_results_overview = reverse("task-results-overview", kwargs=V1)
    response = client.get(f"{live_server.url}{task_results_overview}", headers={"Authorization": f"Token {admin_user.auth_token.key}"})
    assert response.status_code == 200

    upcoming_tasks = reverse("upcoming-tasks", kwargs=V1)
    response = client.get(f"{live_server.url}{upcoming_tasks}", headers={"Authorization": f"Token {admin_user.auth_token.key}"})
    assert response.status_code == 200

    user_list = reverse("user-list", kwargs=V1)
    response = client.get(f"{live_server.url}{user_list}", headers={"Authorization": f"Token {admin_user.auth_token.key}"})
    assert response.status_code == 200
    

def test_user_cannot_view_user_detail(settings, live_server, user_client, user):
    kws = {"pk": user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    response = user_client.get(f"{live_server.url}{user_detail}", headers={"Authorization": f"Token {user.auth_token.key}"})
    assert response.status_code == 403

def test_user_cannot_view_user_detail_role_change(settings, live_server, alt_user):
    client = RequestsClient()
    alt_user.is_superuser = True
    alt_user.save()
    kws = {"pk": alt_user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    response = client.get(f"{live_server.url}{user_detail}", headers={"Authorization": f"Token {alt_user.auth_token.key}"})
    assert response.status_code == 200

    alt_user.is_superuser = False
    alt_user.save()
    kws = {"pk": alt_user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    response = client.get(f"{live_server.url}{user_detail}", headers={"Authorization": f"Token {alt_user.auth_token.key}"})
    assert response.status_code == 403

def test_admin_can_view_user_detail(settings, live_server, admin_user):
    client = RequestsClient()
    kws = {"pk": admin_user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    response = client.get(f"{live_server.url}{user_detail}", headers={"Authorization": f"Token {admin_user.auth_token.key}"})
    assert response.status_code == 200

def test_admin_can_view_other_user_detail(settings, live_server, admin_user, alt_admin_user):
    client = RequestsClient()

    kws = {"pk": alt_admin_user.pk}
    kws.update(V1)
    print(f"kws = {kws}")
    user_detail = reverse("user-detail", kwargs=kws)
    response = client.get(f"{live_server.url}{user_detail}", headers={"Authorization": f"Token {admin_user.auth_token.key}"})
    assert response.status_code == 200

def test_token_visible(settings, live_server, admin_user):
    client = RequestsClient()
    kws = {"pk": admin_user.pk}
    kws.update(V1)
    user_detail = reverse("user-detail", kwargs=kws)
    response = client.get(f"{live_server.url}{user_detail}", headers={"Authorization": f"Token {admin_user.auth_token.key}"})
    assert response.status_code == 200
    assert response.json()["auth_token"] == admin_user.auth_token.key