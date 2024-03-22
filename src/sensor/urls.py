"""scos_sensor URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/

Examples:

Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))

"""

from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView
from rest_framework.urlpatterns import format_suffix_patterns

from . import settings
from .views import api_v1_root_view

DEFAULT_API_VERSION = settings.REST_FRAMEWORK["DEFAULT_VERSION"]

api_urlpatterns = format_suffix_patterns(
    (
        path("", api_v1_root_view, name="api-root"),
        path("capabilities/", include("capabilities.urls")),
        path("schedule/", include("schedule.urls")),
        path("status", include("status.urls")),
        path("users/", include("authentication.urls")),
        path("tasks/", include("tasks.urls")),
        path(
            "schema/",
            SpectacularAPIView.as_view(api_version=DEFAULT_API_VERSION),
            name="schema",
        ),
        path("docs/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    )
)

# Modify admin portal before including url

# Text to put in each page's <h1> (and above login form).
admin.site.site_header = "SCOS Sensor Configuration Portal"

# Text to put at the top of the admin index page.
admin.site.index_title = "SCOS Sensor Configuration Portal"

urlpatterns = [
    path("", RedirectView.as_view(url="/api/")),
    path("admin/", admin.site.urls),
    path("api/", RedirectView.as_view(url=f"/api/{DEFAULT_API_VERSION}/")),
    re_path(settings.API_PREFIX_REGEX, include(api_urlpatterns)),
    path(f"api/auth/", include("knox.urls")),
]
