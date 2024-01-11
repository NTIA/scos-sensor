import importlib
import logging
import pkgutil

from scos_actions.actions import action_classes
from scos_actions.discover import test_actions
from scos_actions.signals import register_action
from scos_actions.discover import init


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
action_types = {}
action_types.update(action_classes)
signal_analyzer = None
gps = None
discovered_actions = {}
if settings.MOCK_SIGAN or settings.RUNNING_TESTS:
    for name, action in test_actions.items():
        logger.debug("test_action: " + name + "=" + str(action))
        register_action.send(sender=__name__, action=action)
else:
    for name, module in discovered_plugins.items():
        logger.debug("Looking for actions in " + name + ": " + str(module))
        discover = importlib.import_module(name + ".discover")
        if hasattr(discover, "actions"):
            for name, action in discover.actions.items():
                logger.debug("action: " + name + "=" + str(action))
                discovered_actions[name] = action
        if hasattr(discover, "action_types") and discover.action_types is not None:
            action_types.update(discover.action_types)
            if hasattr(discover, "signal_analzyer") and discover.signal_analyzer is not None:
                if signal_analyzer is not None:
                    raise Exception("Multiple signal analyzers discovered.")
                signal_analyzer = discover.signal_analzyer
        if hasattr(discover, "gps") and discover.gps is not None:
            gps = discover.gps

if sigan is None:
    raise Exception("No signal analyzer found.")
#Ensure all actions have a sigan
logger.debug("Ensuring actions have signal analyzer.")
for name, action in discovered_actions.items():
    if action.signal_analzyer is None:
        logger.debug(f"Setting signal analyzer for {name}")
        action.set_signal_analyzer(sigan)
    if gps is not None and action.gps is None:
        logger.debug(f"Setting gps for {name}")
        action.gps = gps


logger.debug(f"Loading actions in {settings.ACTIONS_DIR}")
yaml_actions, yaml_test_actions = init(sigan=sigan, action_classes = action_types, yaml_dir=settings.ACTIONS_DIR)
discovered_actions.update(yaml_actions)

for name, action in discovered_actions.items():
    logger.debug("action: " + name + "=" + str(action))
    register_action.send(sender=__name__, action=action)

logger.debug("Finished loading  and registering actions")

