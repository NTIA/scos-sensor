"""Monitor the on-board USRP and touch or remove an indicator file."""

from __future__ import absolute_import

import os
import logging

from hardware import usrp_iface
from sensor.settings import SDR_HEALTHCHECK_FILE
from sensor.utils import touch
from .base import Action


logger = logging.getLogger(__name__)


class UsrpMonitor(Action):
    """Monitor USRP connection and restart container if unreachable."""
    def __init__(self, admin_only=True):
        super(UsrpMonitor, self).__init__(admin_only=admin_only)

        self.usrp = usrp_iface

    def __call__(self, name, tid):
        healthy = True

        logger.debug("Performing USRP health check")
        self.test_required_components()

        requested_samples = 100000  # Issue #42 hit error at ~70k, so test more

        detail = ""

        if healthy:
            try:
                data = self.usrp.radio.acquire_samples(requested_samples)
            except Exception:
                detail = "Unable to acquire USRP"
                healthy = False

        if healthy:
            if not len(data) == requested_samples:
                detail = "USRP data doesn't match request"
                healthy = False

        if healthy:
            try:
                os.remove(SDR_HEALTHCHECK_FILE)
                logger.info("USRP healthy")
            except OSError:
                pass
        else:
            logger.warn("USRP unhealthy")
            touch(SDR_HEALTHCHECK_FILE)
            raise RuntimeError(detail)

    def test_required_components(self):
        """Fail acquisition if a required component is not available."""
        self.usrp.connect()
        if not self.usrp.is_available:
            msg = "acquisition failed: USRP required but not available"
            raise RuntimeError(msg)
