"""A simple example action that logs a message."""

import operator
from collections import OrderedDict

from marshmallow import Schema, fields
from marshmallow.validate import OneOf

from commsensor.logging import log, VALID_LOGLEVELS

from .base import Action
from .utils import one_line


NAMES, LVLS = zip(*sorted(VALID_LOGLEVELS.items(), key=operator.itemgetter(1)))
DEFAULT_LOGLVL = 20
LOGLVL_ERR = "{input!r} is not one of {choices!} corresponding to {labels!r}"


schema_extras = OrderedDict([
    ("msg", {
        "description": one_line(
            """Any occurance of `{edid}` in `msg` will be replaced with the
            parent event descriptor's id. Any occurance of `{eid}` in `msg`
            will be replaced with the sequential event id."""
        )
    }),
    ("loglvl", {
        "description": ("Log level to use, where 50=CRITICAL, 40=ERROR, "
                        "30=WARNING, 20=INFO, 10=DEBUG, and 0=NOTSET")
    })
])


class Logger(Action):
    def __call__(self, edid, eid):
        log.log(level=self.loglvl, msg=self.msg.format(edid=edid, eid=eid))


class LoggerSchema(Schema):
    msg = fields.String(default="running {edid}/{eid}", **schema_extras["msg"])
    loglvl = fields.Integer(validate=OneOf(choices=LVLS, labels=NAMES,
                                           error=LOGLVL_ERR),
                            default=DEFAULT_LOGLVL, **schema_extras["loglvl"])


schema = LoggerSchema(strict=True)
logger = Logger(schema)
