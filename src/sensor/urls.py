"""scos_sensor URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/

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

from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from rest_framework.urlpatterns import format_suffix_patterns

from . import settings
from .views import api_v1_root, schema_view

# Matches api/v1, api/v2, etc...
API_PREFIX = r"^api/(?P<version>v[0-9]+)/"
DEFAULT_API_VERSION = settings.REST_FRAMEWORK["DEFAULT_VERSION"]

api_urlpatterns = format_suffix_patterns(
    (
        path("", api_v1_root, name="api-root"),
        path("capabilities/", include("capabilities.urls")),
        path("schedule/", include("schedule.urls")),
        path("status", include("status.urls")),
        path("users/", include("authentication.urls")),
        path("tasks/", include("tasks.urls")),
        path(
            "schema/", schema_view.with_ui("redoc", cache_timeout=0), name="api_schema"
        ),
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
    path("api/", RedirectView.as_view(url="/api/{}/".format(DEFAULT_API_VERSION))),
    re_path(API_PREFIX, include(api_urlpatterns)),
    path("api/auth/", include("rest_framework.urls")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = (
        [path("__debug__/", include(debug_toolbar.urls))]
        + list(urlpatterns)
        + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    )
