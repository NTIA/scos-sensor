import logging
from . import sensors

logger = logging.getLogger(__name__)

def sensor_registered(sender, **kwargs):
    sensor = kwargs["sensor"]
    if len(sensors) > 0:
        sensors[0] = sensor
    else:
        sensors.append(sensor)
    logger.debug(f"Registered sensor {sensor}")