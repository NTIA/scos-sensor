import hashlib
import importlib
import json
import logging
from pathlib import Path
from its_preselector.configuration_exception import ConfigurationException
from its_preselector.controlbyweb_web_relay import ControlByWebWebRelay

from scos_actions import utils
from scos_actions.signals import register_component_with_status

logger = logging.getLogger(__name__)

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


def load_preselector_from_file(preselector_config_file: Path):
    if preselector_config_file is None:
        return None
    else:
        try:
            preselector_config = utils.load_from_json(preselector_config_file)
            return load_preselector(
                preselector_config, settings.PRESELECTOR_MODULE, settings.PRESELECTOR_CLASS
            )
        except ConfigurationException:
            logger.exception(
                f"Unable to create preselector defined in: {preselector_config_file}"
            )
    return None


def load_preselector(preselector_config, module, preselector_class_name, sensor_definition):
    if module is not None and preselector_class_name is not None:
        preselector_module = importlib.import_module(module)
        preselector_constructor = getattr(preselector_module, preselector_class_name)
        ps = preselector_constructor(sensor_definition, preselector_config)
        if ps and ps.name:
            logger.debug(f"Registering {ps.name} as status provider")
            register_component_with_status.send(__name__, component=ps)
    else:
        ps = None
    return ps


def load_capabilities(sensor_definition_file):
    capabilities = {}
    SENSOR_DEFINITION_HASH = None
    SENSOR_LOCATION = None

    logger.debug(f"Loading {sensor_definition_file}")
    try:
        capabilities["sensor"] = utils.load_from_json(sensor_definition_file)
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
            SENSOR_DEFINITION_HASH = hashlib.sha512(sensor_def.encode("UTF-8")).hexdigest()
            capabilities["sensor"]["sensor_sha512"] = SENSOR_DEFINITION_HASH
    except:
        capabilities["sensor"]["sensor_sha512"] = "ERROR GENERATING HASH"
        # SENSOR_DEFINITION_HASH is None, do not raise Exception
        logger.exception(f"Unable to generate sensor definition hash")

    return capabilities

