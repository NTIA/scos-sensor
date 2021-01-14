from django.conf import settings
from django.contrib.auth import views
from django.urls import path

from authentication.views import oauth_login_callback, oauth_login_view

urlpatterns = (
    path("oauth2/", oauth_login_view, name="oauth-login"),
    path(f"oauth2/code/{settings.FQDN}", oauth_login_callback, name="oauth-callback"),
    # https://github.com/encode/django-rest-framework/blob/master/rest_framework/urls.py
    path("oauth2/logout/", views.LogoutView.as_view(), name="oauth-logout"),
)
