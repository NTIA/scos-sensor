# -*- coding: utf-8 -*-

import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response

import actions
from capabilities import get_capabilities

logger = logging.getLogger(__name__)


def get_actions(include_admin_actions=False):
    serialized_actions = []
    for action in actions.by_name:
        serialized_actions.append(
            {
                "name": action,
                "summary": actions.get_summary(actions.by_name[action]),
                "description": actions.by_name[action].description,
            }
        )

    return serialized_actions


@api_view()
def capabilities_view(request, version, format=None):
    """The capabilites of the sensor."""
    filtered_actions = get_actions(include_admin_actions=request.user.is_staff)
    capabilities = get_capabilities()
    capabilities["actions"] = filtered_actions
    return Response(capabilities)
