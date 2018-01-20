"""A simple example action that logs a message."""

from __future__ import absolute_import

import logging

from .base import Action


logger = logging.getLogger(__name__)

LOGLVL_INFO = 20
LOGLVL_ERROR = 40


class Logger(Action):
    """Log the message "running test {name}/{tid}".

    This is useful for testing and debugging.

    `{name}` will be replaced with the parent schedule entry's name, and
    `{tid}` will be replaced with the sequential task id.

    """
    def __init__(self, loglvl=LOGLVL_INFO, admin_only=False):
        super(Logger, self).__init__(admin_only=admin_only)
        self.loglvl = loglvl

    def __call__(self, req, name, tid):
        msg = "running test {name}/{tid}"
        logger.log(level=self.loglvl, msg=msg.format(name=name, tid=tid))
