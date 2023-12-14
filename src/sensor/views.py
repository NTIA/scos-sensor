from functools import partial

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from utils.docs import API_RESPONSE_405, FORMAT_QUERY_KWARGS, view_docstring

from . import settings
from .serializers import ApiRootSerializer

# API ROOT VIEW
api_root_view_desc = (
    "The root API endpoint provides links to all other API endpoints.\n"
    "The entire API is discoverable by following these links."
)


@extend_schema(
    description=api_root_view_desc,
    summary="SCOS Sensor (API Root)",
    tags=["Discover"],
    responses={200: ApiRootSerializer(), **API_RESPONSE_405},
    **FORMAT_QUERY_KWARGS,
)
@api_view()
@view_docstring(api_root_view_desc)
def api_v1_root_view(request, version, format=None):
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
