# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals

import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response

import actions

from .models import SensorDefinition
from .serializers import SensorDefinitionSerializer


logger = logging.getLogger(__name__)


def get_actions(include_admin_actions=False):
    serialized_actions = []
    for action in actions.by_name:
        if actions.by_name[action].admin_only and not include_admin_actions:
            continue

        serialized_actions.append({
            'name': action,
            'summary': actions.get_summary(actions.by_name[action]),
            'description': actions.by_name[action].description
        })

    return serialized_actions


def get_sensor_definition():
    """Returns SensorDefinition JSON if set or None and logs an error."""
    try:
        sensor_def = SensorDefinition.objects.get()
        return SensorDefinitionSerializer(sensor_def).data
    except SensorDefinition.DoesNotExist:
        logger.error("You must create a SensorDefinition in /admin.")
        return None


@api_view()
def capabilities(request, version, format=None):
    """The capabilites of the sensor."""
    capabilities = {}
    sensor_def = get_sensor_definition()
    capabilities['sensor_definition'] = sensor_def
    filtered_actions = get_actions(include_admin_actions=request.user.is_staff)
    capabilities['actions'] = filtered_actions
    return Response(capabilities)
