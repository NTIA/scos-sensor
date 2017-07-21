"""A simple example action that logs a message."""

import logging
import operator

from rest_framework import serializers

from sensor.logging import VALID_LOGLEVELS

from .base import Action


logger = logging.getLogger(__name__)

names, lvls = zip(*sorted(VALID_LOGLEVELS.items(), key=operator.itemgetter(1)))
LOGLVL_CHOICES = list(zip(lvls, names))
DEFAULT_LOGLVL = 20

msg_help = ("Any occurance of `{seid}` in `msg` will be replaced with the "
            "parent schedule entry's id. Any occurance of `{tid}` in `msg` "
            "will be replaced with the sequential task id.")

lvl_help = ("Log level to use, where 50=CRITICAL, 40=ERROR, "
            "30=WARNING, 20=INFO, 10=DEBUG, and 0=NOTSET")


class Logger(Action):
    def __init__(self, msg, loglvl):
        self.msg = msg
        self.loglvl = loglvl

    def __call__(self, seid, tid):
        logger.log(level=self.loglvl, msg=self.msg.format(seid=seid, tid=tid))


class LoggerSerializer(serializers.Serializer):
    msg = serializers.CharField(max_length=50,
                                default="running {seid}/{tid}",
                                help_text=msg_help)
    loglvl = serializers.ChoiceField(choices=LOGLVL_CHOICES,
                                     default=DEFAULT_LOGLVL,
                                     help_text=lvl_help)

    def create(self, validated_data):
        return Logger(**validated_data)
