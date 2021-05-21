# -*- coding: utf-8 -*-

import logging

from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save
from scos_actions.actions.interfaces.signals import (
    location_action_completed,
    measurement_action_completed,
    monitor_action_completed,
)

logger = logging.getLogger(__name__)


class HandlersConfig(AppConfig):
    name = "handlers"

    def ready(self):
        from handlers.django_handlers import post_delete_callback, post_save_callback
        from handlers.location_handler import location_action_completed_callback
        from handlers.measurement_handler import measurement_action_completed_callback
        from handlers.monitor_handler import monitor_action_completed_callback

        measurement_action_completed.connect(measurement_action_completed_callback)
        logger.debug(
            "measurement_action_completed_callback registered to measurement_action_completed"
        )
        location_action_completed.connect(location_action_completed_callback)
        logger.debug(
            "location_action_completed_callback registered to location_action_completed"
        )

        monitor_action_completed.connect(monitor_action_completed_callback)
        logger.debug(
            "monitor_action_completed_callback registered to monitor_action_completed"
        )

        post_delete.connect(post_delete_callback)
        logger.debug("post_delete_callback registered to post_delete")

        post_save.connect(post_save_callback)
        logger.debug("post_save_callback registered to post_save")
