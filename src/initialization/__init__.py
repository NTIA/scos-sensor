import hashlib
import importlib
import json
import logging
import pkgutil
import shutil
from os import path
from pathlib import Path
from its_preselector.configuration_exception import ConfigurationException
from its_preselector.controlbyweb_web_relay import ControlByWebWebRelay

from scos_actions.actions import action_classes
from scos_actions.discover import test_actions
from scos_actions.discover import init
from scos_actions import utils
from scos_actions.signals import register_component_with_status

from scos_actions.calibration.calibration import Calibration, load_from_json

logger = logging.getLogger(__name__)



def copy_driver_files(driver_dir):
    """Copy driver files where they need to go"""
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
                        source_path = os.path.join(
                            driver_dir, scos_file["source_path"]
                        )
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

def load_switches(switch_dir: Path) -> dict:
    switch_dict = {}
    if switch_dir is not None and switch_dir.is_dir():
        for f in switch_dir.iterdir():
            file_path = f.resolve()
            logger.debug(f"loading switch config {file_path}")
            conf = utils.load_from_json(file_path)
            try:
                switch = ControlByWebWebRelay(conf)
                logger.debug(f"Adding {switch.id}")

                switch_dict[switch.id] = switch
                logger.debug(f"Registering switch status for {switch.name}")
                register_component_with_status.send(__name__, component=switch)
            except ConfigurationException:
                logger.error(f"Unable to configure switch defined in: {file_path}")

    return switch_dict


def load_preselector_from_file(preselector_module, preselector_class, preselector_config_file: Path):
    if preselector_config_file is None:
        return None
    else:
        try:
            preselector_config = utils.load_from_json(preselector_config_file)
            return load_preselector(
                preselector_config, preselector_module, preselector_class
            )
        except ConfigurationException:
            logger.exception(
                f"Unable to create preselector defined in: {preselector_config_file}"
            )
    return None


def load_preselector(preselector_config: str, module: str, preselector_class_name: str, sensor_definition: dict):
    logger.debug(f"loading {preselector_class_name} from {module} with config: {preselector_config}")
    if module is not None and preselector_class_name is not None:
        preselector_module = importlib.import_module(module)
        preselector_constructor = getattr(preselector_module, preselector_class_name)
        preselector_config = utils.load_from_json(preselector_config)
        ps = preselector_constructor(sensor_definition, preselector_config)
        register_component_with_status.send(ps, component=ps)
    else:
        ps = None
    return ps





def get_sigan_calibration(sigan_cal_file_path: str, default_cal_file_path: str) -> Calibration:
    """
    Load signal analyzer calibration data from file.

    :param sigan_cal_file_path: Path to JSON file containing signal
        analyzer calibration data.
    :param default_cal_file_path: Path to the default cal file.
    :return: The signal analyzer ``Calibration`` object.
    """
    try:
        sigan_cal = None
        if sigan_cal_file_path is None or sigan_cal_file_path == "":
            logger.warning("No sigan calibration file specified. Not loading calibration file.")
        elif not path.exists(sigan_cal_file_path):
            logger.warning(
                sigan_cal_file_path + " does not exist. Not loading sigan calibration file."
            )
        else:
            logger.debug(f"Loading sigan cal file: {sigan_cal_file_path}")
            default = check_for_default_calibration(sigan_cal_file_path,default_cal_file_path, "Sigan")
            sigan_cal = load_from_json(sigan_cal_file_path, default)
            sigan_cal.is_default = default
    except Exception:
        sigan_cal = None
        logger.exception("Unable to load sigan calibration data, reverting to none")
    return sigan_cal


def get_sensor_calibration(sensor_cal_file_path: str, default_cal_file_path: str) -> Calibration:
    """
    Load sensor calibration data from file.

    :param sensor_cal_file_path: Path to JSON file containing sensor
        calibration data.
    :param default_cal_file_path: Name of the default calibration file.
    :return: The sensor ``Calibration`` object.
    """
    try:
        sensor_cal = None
        if sensor_cal_file_path is None or sensor_cal_file_path == "":
            logger.warning(
                "No sensor calibration file specified. Not loading calibration file."
            )
        elif not path.exists(sensor_cal_file_path):
            logger.warning(
                sensor_cal_file_path
                + " does not exist. Not loading sensor calibration file."
            )
        else:
            logger.debug(f"Loading sensor cal file: {sensor_cal_file_path}")
            default = check_for_default_calibration(
                sensor_cal_file_path, default_cal_file_path, "Sensor"
            )
        sensor_cal = load_from_json(sensor_cal_file_path, default)
        sensor_cal.is_default = default
    except Exception:
        sensor_cal = None
        logger.exception("Unable to load sensor calibration data, reverting to none")
    return sensor_cal


def check_for_default_calibration(cal_file_path: str,default_cal_path: str, cal_type: str) -> bool:
    default_cal = False
    if cal_file_path == default_cal_path:
        default_cal = True
        logger.warning(
            f"***************LOADING DEFAULT {cal_type} CALIBRATION***************"
        )
    return default_cal


def load_capabilities(sensor_definition_file):
    capabilities = {}
    sensor_definition_hash = None
    sensor_location = None

    logger.debug(f"Loading {sensor_definition_file}")
    try:
        capabilities["sensor"] = load_from_json(sensor_definition_file)
    except Exception as e:
        logger.warning(
            f"Failed to load sensor definition file: {sensor_definition_file}"
            + "\nAn empty sensor definition will be used"
        )
        capabilities["sensor"] = {"sensor_spec": {"id": "unknown"}}
        capabilities["sensor"]["sensor_sha512"] = "UNKNOWN SENSOR DEFINITION"

    # Generate sensor definition file hash (SHA 512)
    try:
        if "sensor_sha512" not in capabilities["sensor"]:
            sensor_def = json.dumps(capabilities["sensor"], sort_keys=True)
            sensor_definition_hash = hashlib.sha512(sensor_def.encode("UTF-8")).hexdigest()
            capabilities["sensor"]["sensor_sha512"] = sensor_definition_hash
    except:
        capabilities["sensor"]["sensor_sha512"] = "ERROR GENERATING HASH"
        # SENSOR_DEFINITION_HASH is None, do not raise Exception, but log it
        logger.exception(f"Unable to generate sensor definition hash")

    return capabilities

def load_actions(mock_sigan, running_tests, driver_dir, action_dir):
    logger.debug("********** Initializing actions **********")

    copy_driver_files(driver_dir)  # copy driver files before loading plugins
    discovered_plugins = {
        name: importlib.import_module(name)
        for finder, name, ispkg in pkgutil.iter_modules()
        if name.startswith("scos_") and name != "scos_actions"
    }
    logger.debug(discovered_plugins)
    action_types = {}
    action_types.update(action_classes)
    actions = {}
    if mock_sigan or running_tests:
        for name, action in test_actions.items():
            logger.debug("test_action: " + name + "=" + str(action))
    else:
        for name, module in discovered_plugins.items():
            logger.debug("Looking for actions in " + name + ": " + str(module))
            discover = importlib.import_module(name + ".discover")
            if hasattr(discover, "actions"):
                logger.debug(f"loading {len(discover.actions)} actions.")
                actions.update(discover.actions)
            if hasattr(discover, "action_types") and discover.action_types is not None:
                action_types.update(discover.action_types)

    logger.debug(f"Loading actions in {action_dir}")
    yaml_actions, yaml_test_actions = init(action_classes = action_types, yaml_dir=action_dir)
    actions.update(yaml_actions)
    logger.debug("Finished loading  and registering actions")
    return actions