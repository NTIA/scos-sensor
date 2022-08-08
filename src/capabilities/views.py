# -*- coding: utf-8 -*-
import copy
import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response

from actions import get_summary
from capabilities import actions, capabilities

logger = logging.getLogger(__name__)


def get_actions(include_admin_actions=False):
    serialized_actions = []
    for action in actions:
        serialized_actions.append(
            {
                "name": action,
                "summary": get_summary(actions[action]),
                "description": actions[action].description,
            }
        )

    return serialized_actions


@api_view()
def capabilities_view(request, version, format=None):
    """The capabilites of the sensor."""
    filtered_actions = get_actions(include_admin_actions=request.user.is_staff)
    filtered_capabilities = copy.deepcopy(capabilities)
    filtered_capabilities["actions"] = filtered_actions
    return Response(filtered_capabilities)
