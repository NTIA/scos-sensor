import importlib
import json
import logging
import os
import pkgutil
import shutil
from typing import Dict

from django.conf import settings
from scos_actions.actions import action_classes
from scos_actions.discover import init, test_actions
from scos_actions.interfaces.action import Action

logger = logging.getLogger(__name__)


class ActionLoader:
    """
    Loads actions from scos_ plugins and any yaml configurations
    in the configs/actions directory. Note: this class is a
    singleton so other applications may safely create an instance
    and reference the .actions property.
    """

    _instance = None

    def __init__(self):
        if not hasattr(self, "actions"):
            logger.debug("Actions have not been loaded. Loading actions...")
            self._actions = load_actions(
                settings.MOCK_SIGAN,
                settings.RUNNING_TESTS,
                settings.DRIVERS_DIR,
                settings.ACTIONS_DIR,
            )
        else:
            logger.debug("Already loaded actions. ")

    def __new__(cls):
        if cls._instance is None:
            logger.debug("Creating the ActionLoader")
            cls._instance = super().__new__(cls)
            logger.debug(
                f"Calling load_actions with {settings.MOCK_SIGAN}, {settings.RUNNING_TESTS}, {settings.DRIVERS_DIR}, {settings.ACTIONS_DIR}"
            )
        return cls._instance

    @property
    def actions(self) -> Dict[str, Action]:
        """
        Returns all sensor actions configured in the system.
        """
        return self._actions


def copy_driver_files(driver_dir: str):
    """Copy driver files where they need to go"""
    logger.debug(f"Copying driver files in {driver_dir}")
    for root, dirs, files in os.walk(driver_dir):
        for filename in files:
            name_without_ext, ext = os.path.splitext(filename)
            if ext.lower() == ".json":
                json_data = {}
                file_path = os.path.join(root, filename)
                with open(file_path) as json_file:
                    json_data = json.load(json_file)
                if type(json_data) == dict and "scos_files" in json_data:
                    scos_files = json_data["scos_files"]
                    for scos_file in scos_files:
                        source_path = os.path.join(driver_dir, scos_file["source_path"])
                        if not os.path.isfile(source_path):
                            logger.error(f"Unable to find file at {source_path}")
                            continue
                        dest_path = scos_file["dest_path"]
                        dest_dir = os.path.dirname(dest_path)
                        try:
                            if not os.path.isdir(dest_dir):
                                os.makedirs(dest_dir)
                            logger.debug(f"copying {source_path} to {dest_path}")
                            shutil.copyfile(source_path, dest_path)
                        except Exception as e:
                            logger.error(f"Failed to copy {source_path} to {dest_path}")
                            logger.error(e)


def load_actions(
    mock_sigan: bool, running_tests: bool, driver_dir: str, action_dir: str
):
    logger.debug("********** Initializing actions **********")
    copy_driver_files(driver_dir)  # copy driver files before loading plugins
    discovered_plugins = {
        name: importlib.import_module(name)
        for finder, name, ispkg in pkgutil.iter_modules()
        if name.startswith("scos_") and name != "scos_actions"
    }
    logger.debug(discovered_plugins)
    actions = {}
    if mock_sigan or running_tests:
        logger.debug(f"Loading {len(test_actions)} test actions.")
        actions.update(test_actions)
    else:
        for name, module in discovered_plugins.items():
            logger.debug("Looking for actions in " + name + ": " + str(module))
            discover = importlib.import_module(name + ".discover")
            if hasattr(discover, "actions"):
                logger.debug(f"loading {len(discover.actions)} actions.")
                actions.update(discover.actions)
            if (
                hasattr(discover, "action_classes")
                and discover.action_classes is not None
            ):
                action_classes.update(discover.action_classes)

    logger.debug(f"Loading actions in {action_dir}")
    yaml_actions, yaml_test_actions = init(
        action_classes=action_classes, yaml_dir=action_dir
    )
    actions.update(yaml_actions)
    logger.debug("Finished loading  and registering actions")
    return actions
