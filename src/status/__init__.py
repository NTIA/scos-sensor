import datetime
import logging
from initialization import sensor_loader

logger = logging.getLogger(__name__)
logger.debug("********** Initializing status **********")
if sensor_loader.sigan is not None:
    start_time = sensor_loader.sensor.start_time
else:
    start_time =  datetime.datetime.utcnow()