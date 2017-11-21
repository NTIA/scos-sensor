"""A simple example action that logs a message."""

from __future__ import absolute_import

import logging
import platform
from itertools import compress

import docker

from .base import Action
from . import usrp


logger = logging.getLogger(__name__)


docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')


class USRPMonitor(Action):
    """Monitor USRP connection and restart container if unreachable."""
    def __init__(self, admin_only=True):
        super(USRPMonitor, self).__init__(admin_only=admin_only)

        self.usrp = usrp  # make instance variable to allow hotswapping mock

    def __call__(self, name, tid):
        healthy = True
        this_container = docker_client.containers.get(platform.node())

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

        if not healthy:
            logger.warn("Restarting container")
            this_container.restart()
