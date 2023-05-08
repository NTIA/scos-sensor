from functools import partial

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from . import settings


@api_view(("GET",))
def api_v1_root(request, version, format=None):
    """SCOS sensor API root."""
    reverse_ = partial(reverse, request=request, format=format)
    list_endpoints = {
        "capabilities": reverse_("capabilities"),
        "schedule": reverse_("schedule-list"),
        "status": reverse_("status"),
        "tasks": reverse_("task-root"),
        "users": reverse_("user-list"),
    }

    # See note in settings:INTERNAL_IPS about why we do this here
    nginx_container_ip = request.META["REMOTE_ADDR"]
    nginx_ip_set = nginx_container_ip in settings.INTERNAL_IPS
    if settings.IN_DOCKER and settings.DEBUG and not nginx_ip_set:
        settings.INTERNAL_IPS.append(nginx_container_ip)

    return Response(list_endpoints)
