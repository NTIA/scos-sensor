from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework.settings import api_settings

from . import settings


schema_view = get_schema_view(
    openapi.Info(
        title=settings.API_TITLE,
        default_version=api_settings.DEFAULT_VERSION,
        description=settings.API_DESCRIPTION,
        contact=openapi.Contact(email="sms@ntia.doc.gov"),
        license=openapi.License(name="NTIA/ITS", url=settings.LICENSE_URL),
    ),
    public=False,
    permission_classes=(permissions.IsAuthenticated, ),
)
