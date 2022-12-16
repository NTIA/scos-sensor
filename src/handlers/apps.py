import logging

from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save
from scos_actions.signals import (
    location_action_completed,
    measurement_action_completed,
    trigger_api_restart,
)

logger = logging.getLogger(__name__)


class HandlersConfig(AppConfig):
    name = "handlers"

    def ready(self):
        from handlers.health_check_handler import trigger_api_restart_callback
        from handlers.location_handler import (
            db_location_deleted,
            db_location_updated,
            location_action_completed_callback,
        )
        from handlers.measurement_handler import measurement_action_completed_callback

        measurement_action_completed.connect(measurement_action_completed_callback)
        logger.debug(
            "measurement_action_completed_callback registered to measurement_action_completed"
        )
        location_action_completed.connect(location_action_completed_callback)
        logger.debug(
            "location_action_completed_callback registered to location_action_completed"
        )
        post_save.connect(db_location_updated)
        logger.debug("db_location_updated registered to post_save")

        post_delete.connect(db_location_deleted)
        logger.debug("db_location_deleted registered to post_delete")

        trigger_api_restart.connect(trigger_api_restart_callback)
        logger.debug(
            "monitor_action_completed_callback registered to monitor_action_completed"
        )
