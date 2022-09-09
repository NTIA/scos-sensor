import datetime
import logging

from scos_actions.calibration import sensor_calibration

logger = logging.getLogger(__name__)
logger.debug("********** Initializing status **********")
sensor_cal = sensor_calibration
start_time = datetime.datetime.utcnow()
