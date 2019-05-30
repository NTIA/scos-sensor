import logging
from pathlib import Path

from ruamel.yaml import YAML

from sensor import settings

from . import logger as logger_action
from .acquire_single_freq_fft import SingleFrequencyFftAcquisition
from .acquire_stepped_freq_tdomain_iq import SteppedFrequencyTimeDomainIqAcquisition
from .monitor_usrp import UsrpMonitor
from .sync_gps import SyncGps


logger = logging.getLogger(__name__)


# Actions initialized here are made available through the API
registered_actions = {
    "logger": logger_action.Logger(),
    "admin_logger": logger_action.Logger(
        loglvl=logger_action.LOGLVL_ERROR, admin_only=True
    ),
    "monitor_usrp": UsrpMonitor(admin_only=True),
    "sync_gps": SyncGps(admin_only=True),
}

by_name = registered_actions


# Map a class name to an action class
# The YAML loader can key an object with parameters on these class names
action_classes = {
    "logger": logger_action.Logger,
    "usrp_monitor": UsrpMonitor,
    "sync_gps": SyncGps,
    "single_frequency_fft": SingleFrequencyFftAcquisition,
    "stepped_frequency_time_domain_iq": SteppedFrequencyTimeDomainIqAcquisition,
}


def get_action_with_summary(action):
    """Given an action, return the string 'action_name - summary'."""
    action_fn = registered_actions[action]
    summary = get_summary(action_fn)
    action_with_summary = action
    if summary:
        action_with_summary += " - {}".format(summary)

    return action_with_summary


def get_summary(action_fn):
    """Extract the first line of the action's description as a summary."""
    description = action_fn.description
    summary = None
    if description:
        summary = description.splitlines()[0]

    return summary


def load_from_yaml(yaml_dir=settings.ACTION_DEFINITIONS_DIR):
    """Load any YAML files in yaml_dir."""
    yaml = YAML(typ="safe")
    yaml_path = Path(yaml_dir)
    for yaml_file in yaml_path.glob("*.yml"):
        defn = yaml.load(yaml_file)
        for class_name, parameters in defn.items():
            try:
                action = action_classes[class_name](**parameters)
                registered_actions[action.name] = action
            except KeyError as exc:
                err = "Nonexistent action class name {!r} referenced in {!r}"
                logger.error(err.format(class_name, yaml_file.name))
                logger.exception(exc)
                raise exc
            except TypeError as exc:
                err = "Invalid parameter list {!r} referenced in {!r}"
                logger.error(err.format(parameters, yaml_file.name))
                logger.exception(exc)
                raise exc


MAX_LENGTH = 50
VALID_ACTIONS = []
CHOICES = []
ADMIN_CHOICES = []


def init():
    """Allows re-initing VALID_ACTIONS if `registered_actions` is modified."""
    global VALID_ACTIONS
    global CHOICES

    load_from_yaml()

    VALID_ACTIONS = sorted(registered_actions.keys())
    for action in VALID_ACTIONS:
        if registered_actions[action].admin_only:
            ADMIN_CHOICES.append((action, get_action_with_summary(action)))
        else:
            CHOICES.append((action, get_action_with_summary(action)))


init()
