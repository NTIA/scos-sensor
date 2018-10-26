"""Monitor the on-board USRP and touch or remove an indicator file."""

from __future__ import absolute_import

import logging

from hardware import gps_iface
from status.models import Location, GPS_LOCATION_DESCRIPTION

from .base import Action

logger = logging.getLogger(__name__)


class SyncGps(Action):
    """Query the GPS and syncronize time and location."""

    def __init__(self, admin_only=True):
        super(SyncGps, self).__init__(admin_only=admin_only)

        self.gps = gps_iface

    def __call__(self, name, tid):
        logger.debug("Syncing to GPS")

        location = self.gps.get_lat_long()
        if location is None:
            raise RuntimeError("Unable to syncronize to GPS")

        latitude, longitude = location

        try:
            gps_location = Location.objects.get(gps=True)
            gps_location.latitude = latitude
            gps_location.longitude = longitude
            gps_location.save()
        except Location.DoesNotExist:
            gps_location = Location.objects.create(
                gps=True,
                description=GPS_LOCATION_DESCRIPTION,
                latitude=latitude,
                longitude=longitude)
