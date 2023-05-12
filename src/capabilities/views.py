import copy
import logging

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from utils import get_summary
from utils.docs import FORMAT_QUERY_KWARGS, view_docstring

from . import actions_by_name, sensor_capabilities

logger = logging.getLogger(__name__)
logger.debug("scos-sensor/capabilities/views.py")


def get_actions():
    serialized_actions = []
    for action in actions_by_name:
        serialized_actions.append(
            {
                "name": action,
                "summary": get_summary(actions_by_name[action]),
                "description": actions_by_name[action].description,
            }
        )

    return serialized_actions


# CAPABILITIES VIEW
capabilities_view_desc = (
    "The `capabilities` endpoint provides descriptions of the physical "
    "sensor and a list of actions the sensor is capable of performing."
)


@extend_schema(
    description=capabilities_view_desc,
    summary="Sensor Capabilities",
    tags=["Discover"],
    **FORMAT_QUERY_KWARGS,
)
@api_view()
@view_docstring(capabilities_view_desc)
def capabilities_view(request, version, format=None):
    """The capabilites of the sensor."""
    filtered_actions = get_actions()
    filtered_capabilities = copy.deepcopy(sensor_capabilities)
    filtered_capabilities["actions"] = filtered_actions
    return Response(filtered_capabilities)
