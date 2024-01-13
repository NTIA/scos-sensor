# import importlib
# import logging
# import pkgutil
#
# from scos_actions.actions import action_classes
# from scos_actions.discover import test_actions
# from scos_actions.discover import init
#
#
# from sensor import settings
# from sensor.utils import copy_driver_files
#
# logger = logging.getLogger(__name__)
# logger.debug("********** Initializing actions **********")
#
# copy_driver_files()  # copy driver files before loading plugins
#
# discovered_plugins = {
#     name: importlib.import_module(name)
#     for finder, name, ispkg in pkgutil.iter_modules()
#     if name.startswith("scos_") and name != "scos_actions"
# }
# logger.debug(discovered_plugins)
# action_types = {}
# action_types.update(action_classes)
# actions = {}
# if settings.MOCK_SIGAN or settings.RUNNING_TESTS:
#     for name, action in test_actions.items():
#         logger.debug("test_action: " + name + "=" + str(action))
# else:
#     for name, module in discovered_plugins.items():
#         logger.debug("Looking for actions in " + name + ": " + str(module))
#         discover = importlib.import_module(name + ".discover")
#         if hasattr(discover, "actions"):
#             for name, action in discover.actions.items():
#                 logger.debug("action: " + name + "=" + str(action))
#                 actions[name] = action
#         if hasattr(discover, "action_types") and discover.action_types is not None:
#             action_types.update(discover.action_types)
#
#
# logger.debug(f"Loading actions in {settings.ACTIONS_DIR}")
# yaml_actions, yaml_test_actions = init(action_classes = action_types, yaml_dir=settings.ACTIONS_DIR)
# actions.update(yaml_actions)
# logger.debug("Finished loading  and registering actions")
#
