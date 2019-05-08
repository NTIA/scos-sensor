"""Monitor the on-board USRP and touch or remove an indicator file."""

from __future__ import absolute_import

import logging
from pathlib import Path

from hardware import usrp_iface
from sensor import settings
from .base import Action

logger = logging.getLogger(__name__)


class UsrpMonitor(Action):
    """Monitor USRP connection and restart container if unreachable."""

    def __init__(self, admin_only=True):
        super(UsrpMonitor, self).__init__(admin_only=admin_only)

        self.usrp = usrp_iface

    def __call__(self, name, tid):
        logger.debug("Performing USRP health check")

        healthy = True
        detail = ""

        try:
            self.test_required_components()
        except RuntimeError as err:
            healthy = False
            detail = str(err)

        requested_samples = 100000  # Issue #42 hit error at ~70k, so test more

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
                Path(settings.SDR_HEALTHCHECK_FILE).unlink()
                logger.info("USRP healthy")
            except FileNotFoundError:
                pass
        else:
            logger.warning("USRP unhealthy")
            if settings.IN_DOCKER:
                Path(settings.SDR_HEALTHCHECK_FILE).touch()
            raise RuntimeError(detail)

    def test_required_components(self):
        """Fail acquisition if a required component is not available."""
        self.usrp.connect()
        if not self.usrp.is_available:
            msg = "acquisition failed: USRP required but not available"
            raise RuntimeError(msg)
