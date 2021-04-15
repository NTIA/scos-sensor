import importlib
import logging

from actions import discovered_plugins

logger = logging.getLogger(__name__)

last_calibration_time = None

for name, module in discovered_plugins.items():
    logger.debug("Looking for actions in " + name + ": " + str(module))
    discover = importlib.import_module(name + ".discover")
    if hasattr(discover, "get_last_calibration_time"):
        last_calibration_time = discover.get_last_calibration_time
