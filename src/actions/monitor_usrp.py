"""Monitor the on-board USRP and touch or remove an indicator file."""

from __future__ import absolute_import

import os
import logging
from itertools import compress

from sensor.settings import USRP_HEALTHCHECK_FILE
from .base import Action
from . import usrp


logger = logging.getLogger(__name__)


def touch(fname, times=None):
    """Emulates unix `touch` utility."""
    with open(fname, 'a'):
        os.utime(fname, times)


class USRPMonitor(Action):
    """Monitor USRP connection and restart container if unreachable."""
    def __init__(self, admin_only=True):
        super(USRPMonitor, self).__init__(admin_only=admin_only)

        self.usrp = usrp  # make instance variable to allow hotswapping mock

    def __call__(self, name, tid):
        healthy = True

        logger.debug("Performing USRP health check")

        if self.usrp.uhd_is_available and not self.usrp.is_available:
            self.usrp.connect()

        required_components = (
            self.usrp.uhd_is_available,
            self.usrp.is_available
        )
        missing_components = [not rc for rc in required_components]
        component_names = ("UHD", "USRP")
        if any(missing_components):
            missing = tuple(compress(component_names, missing_components))
            logger.warn("{} required but not available".format(missing))
            healthy = False

        requested_samples = 100

        if healthy:
            try:
                data = self.usrp.radio.acquire_samples(requested_samples)
            except Exception:
                logger.exception("Unable to acquire USRP")
                healthy = False

        if healthy:
            if not len(data) == requested_samples:
                logger.warn("USRP data doesn't match request")
                healthy = False

        if healthy:
            try:
                os.remove(USRP_HEALTHCHECK_FILE)
                logger.info("USRP healthy")
            except OSError:
                pass
        else:
            logger.warn("USRP unhealthy")
            touch(USRP_HEALTHCHECK_FILE)
