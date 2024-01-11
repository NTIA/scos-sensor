from collections import OrderedDict

from scos_actions.signals import register_action, register_gps, register_signal_analyzer

from .gps_monitor import GpsMonitor
from .signal_analyzer_monitor import SignalAnalyzerMonitor

registered_actions = OrderedDict()
sigan_monitor = SignalAnalyzerMonitor()
gps_monitor = GpsMonitor()


def add_action_handler(sender, **kwargs):
    action = kwargs["action"]
    registered_actions[action.name] = action


def register_sigan_handler(sender, **kwargs):
    sigan = kwargs["signal_analyzer"]
    sigan_monitor.register_signal_analyzer(sigan)


def register_gps_handler(sender, **kwargs):
    gps = kwargs["gps"]
    gps_monitor.register_gps(gps)


register_action.connect(add_action_handler)
register_signal_analyzer.connect(register_sigan_handler)
register_gps.connect(register_gps_handler)
