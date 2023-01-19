import importlib
import logging
import pkgutil

from scos_actions.discover import test_actions
from scos_actions.signals import register_action

from sensor import settings
from sensor.utils import copy_driver_files

logger = logging.getLogger(__name__)
logger.debug("********** Initializing actions **********")

copy_driver_files()  # copy driver files before loading plugins

discovered_plugins = {
    name: importlib.import_module(name)
    for finder, name, ispkg in pkgutil.iter_modules()
    if name.startswith("scos_") and name != "scos_actions"
}
logger.debug(discovered_plugins)

if settings.MOCK_SIGAN or settings.RUNNING_TESTS:
    for name, action in test_actions.items():
        logger.debug("test_action: " + name + "=" + str(action))
        register_action.send(sender=__name__, action=action)
else:
    for name, module in discovered_plugins.items():
        logger.debug("Looking for actions in " + name + ": " + str(module))
        discover = importlib.import_module(name + ".discover")
        for name, action in discover.actions.items():
            logger.debug("action: " + name + "=" + str(action))
            register_action.send(sender=__name__, action=action)
logger.debug("Finished loading actions")
