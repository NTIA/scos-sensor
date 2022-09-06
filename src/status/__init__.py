import datetime
import logging

from scos_actions.calibration import sensor_calibration

logger = logging.getLogger(__name__)
logger.debug("scos-sensor.status initializing")
sensor_cal = sensor_calibration
start_time = datetime.datetime.utcnow()
