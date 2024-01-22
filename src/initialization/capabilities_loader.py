import hashlib
import json
import logging
from django.conf import settings
from scos_actions.utils import load_from_json

logger = logging.getLogger(__name__)


class CapabilitiesLoader:
    _instance = None

    def __init__(self):
        if not hasattr(self, "capabilities"):
            logger.debug("Capabilities have not been loaded. Loading...")
            self.capabilities = load_capabilities(settings.SENSOR_DEFINITION_FILE)
        else:
            logger.debug("Already loaded capabilities. ")

    def __new__(cls):
        if cls._instance is None:
            logger.debug("Creating the ActionLoader")
            cls._instance = super().__new__(cls)
        return cls._instance


def load_capabilities(sensor_definition_file) -> dict:
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
            sensor_definition_hash = hashlib.sha512(
                sensor_def.encode("UTF-8")
            ).hexdigest()
            capabilities["sensor"]["sensor_sha512"] = sensor_definition_hash
    except:
        capabilities["sensor"]["sensor_sha512"] = "ERROR GENERATING HASH"
        # sensor_sha512 is None, do not raise Exception, but log it
        logger.exception(f"Unable to generate sensor definition hash")

    return capabilities
