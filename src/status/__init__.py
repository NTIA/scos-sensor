import logging
from initialization import sensor_loader

logger = logging.getLogger(__name__)
logger.debug("********** Initializing status **********")
if sensor_loader.sensor is not None:
    start_time = sensor_loader.sensor.start_time
