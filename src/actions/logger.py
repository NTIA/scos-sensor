"""A simple example action that logs a message."""

import logging


logger = logging.getLogger(__name__)

DEFAULT_LOGLVL = 20


class Logger(object):
    """Log the message "running test {seid}/{tid}" at log level INFO.

    This is useful for testing and debugging.

    `{seid}` will be replaced with the parent schedule entry's id, and `{tid}`
    will be replaced with the sequential task id.

    """
    def __call__(self, seid, tid):
        msg = "running test {seid}/{tid}"
        logger.log(level=DEFAULT_LOGLVL, msg=msg.format(seid=seid, tid=tid))
