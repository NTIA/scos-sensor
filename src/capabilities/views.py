import copy
import logging

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from utils import get_summary
from utils.docs import API_RESPONSE_405, FORMAT_QUERY_KWARGS, view_docstring

from . import actions_by_name, sensor_capabilities
from .serializers import CapabilitiesSerializer

logger = logging.getLogger(__name__)
logger.debug("scos-sensor/capabilities/views.py")


def get_capabilities() -> dict:
    filtered_actions = [
        {
            "name": name,
            "summary": get_summary(action),
            "description": action.description,
        }
        for name, action in actions_by_name.items()
    ]
    filtered_capabilities = copy.deepcopy(sensor_capabilities)
    filtered_capabilities["actions"] = filtered_actions
    return filtered_capabilities


# CAPABILITIES VIEW
capabilities_view_desc = (
    "The `capabilities` endpoint provides descriptions of the physical "
    "sensor and a list of actions the sensor is capable of performing."
)


@extend_schema(
    description=capabilities_view_desc,
    summary="Sensor Capabilities",
    tags=["Discover"],
    responses={200: CapabilitiesSerializer(), **API_RESPONSE_405},
    **FORMAT_QUERY_KWARGS,
)
@api_view()
# @authentication_classes()  # TODO: maybe this?
@view_docstring(capabilities_view_desc)
def capabilities_view(request, version, format=None):
    return Response(get_capabilities())
