import logging

logger = logging.getLogger(__name__)


class GpsMonitor:
    def __init__(self):
        logger.debug("Initializing GPS Monitor")
        self._gps = None

    def register_gps(self, gps):
        """
        Registers the GPS so other scos components may access it. The
        registered GPS will be accessible by importing
        gps_monitor from scos_actions.core and accessing the
        gps property.

        :param gps: the instance of a GPSInterface to register.
        """
        logger.debug(f"Setting GPS to {gps}")
        self._gps = gps

    @property
    def gps(self):
        """
        Provides access to the registered GPS.

        :return: the registered instance of a GPSInterface.
        """
        return self._gps
