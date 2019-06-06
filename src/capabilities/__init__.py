from sensor.settings import SENSOR_DEFINITION_FILE

capabilities = {}


def load_from_json(fname):
    import json
    import logging

    logger = logging.getLogger(__name__)

    try:
        with open(fname) as f:
            return json.load(f)
    except Exception:
        logger.exception("Unable to load JSON file {}".format(fname))


capabilities["sensor_definition"] = load_from_json(SENSOR_DEFINITION_FILE)
