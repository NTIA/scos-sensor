"""A simple example action that logs a message."""

import logging


logger = logging.getLogger(__name__)

DEFAULT_LOGLVL = 20


class Logger(object):
    """Log the message "running test {name}/{tid}" at log level INFO.

    This is useful for testing and debugging.

    `{name}` will be replaced with the parent schedule entry's name, and
    `{tid}` will be replaced with the sequential task id.

    """
    def __call__(self, name, tid):
        msg = "running test {name}/{tid}"
        logger.log(level=DEFAULT_LOGLVL, msg=msg.format(name=name, tid=tid))
