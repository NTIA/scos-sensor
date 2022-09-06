# -*- coding: utf-8 -*-
import copy
import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import actions_by_name
from . import sensor_capabilities
from actions import get_summary

logger = logging.getLogger(__name__)
logger.debug("scos-sensor/capabilities/views.py")


def get_actions(include_admin_actions=False):
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


@api_view()
def capabilities_view(request, version, format=None):
    """The capabilites of the sensor."""
    filtered_actions = get_actions(include_admin_actions=request.user.is_staff)
    filtered_capabilities = copy.deepcopy(sensor_capabilities)
    filtered_capabilities["actions"] = filtered_actions
    return Response(filtered_capabilities)
