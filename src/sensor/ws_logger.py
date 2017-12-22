import json
import logging

from channels import Group


VALID_LOGLEVELS = {
    'NOTSET': 0,
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}


class ChannelStream(object):
    def __init__(self, channel):
        self.channel = channel

    def write(self, msg):
        self.channel.send({'text': json.dumps(msg)})


class WebSocketHandler(logging.StreamHandler):
    def __init__(self, *args, **kwargs):
        logs_group = Group('logs')
        ws_channel = ChannelStream(logs_group)
        super(WebSocketHandler, self).__init__(stream=ws_channel)
