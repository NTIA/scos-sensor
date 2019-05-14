from functools import partial

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings

from . import settings


@api_view(('GET', ))
def api_v1_root(request, version, format=None):
    """SCOS sensor API root."""
    reverse_ = partial(reverse, request=request, format=format)
    list_endpoints = {
        'schedule': reverse_('schedule-list'),
        'acquisitions': reverse_('acquisitions-overview'),
        'status': reverse_('status'),
        'users': reverse_('user-list'),
        'capabilities': reverse_('capabilities'),
        'results': reverse_('results-overview')
    }

    # See note in settings:INTERNAL_IPS about why we do this here
    nginx_container_ip = request.META['REMOTE_ADDR']
    nginx_ip_set = nginx_container_ip in settings.INTERNAL_IPS
    if (settings.IN_DOCKER and settings.DEBUG and not nginx_ip_set):
        settings.INTERNAL_IPS.append(nginx_container_ip)

    return Response(list_endpoints)


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
