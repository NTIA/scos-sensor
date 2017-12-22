"""Django channel routing."""

from __future__ import absolute_import

from channels.routing import route
from sensor.consumers import ws_add, ws_message, ws_disconnect


channel_routing = [
    route('websocket.connect', ws_add, path=r'^/logs/$'),
    route('websocket.receive', ws_message, path=r'^/logs/$'),
    route('websocket.disconnect', ws_disconnect),
]
