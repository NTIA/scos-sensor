import datetime
import logging
from scos_actions.signals import register_component_with_status
from scos_actions.signals import register_signal_analyzer
from scos_actions.status.status_monitor import StatusMonitor



signal_analyzers = []
logger = logging.getLogger(__name__)
logger.debug("********** Initializing status **********")
start_time = datetime.datetime.utcnow()
status_monitor = StatusMonitor()

def signal_analyzer_registration_handler(sender, **kwargs):
    try:
        logger.debug(f"Registering {sender} as status provider")
        signal_analyzers[0] = kwargs["signal_analyzer"]
    except:
        logger.exception("Error registering status component")


def status_registration_handler(sender, **kwargs):
    try:
        logger.debug(f"Registering {sender} as status provider")
        status_monitor.add_component(kwargs["component"])
    except:
        logger.exception("Error registering status component")

register_component_with_status.connect(status_registration_handler)
register_signal_analyzer.connect(signal_analyzer_registration_handler)

