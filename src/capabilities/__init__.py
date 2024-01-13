import logging

from django.conf import settings


logger = logging.getLogger(__name__)
logger.debug("********** Initializing capabilities **********")
actions_by_name = settings.ACTIONS
sensor_capabilities = settings.CAPABILITIES
