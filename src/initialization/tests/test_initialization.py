from src.initialization import load_preselector
import logging
import os

logger = logging.getLogger(__name__)

def test_load_preselector():
    preselector_config = os.getcwd()
    index = preselector_config.index("src")
    preselector_config = os.path.join( preselector_config[:index], "configs/preselector_config.json")
    logger.debug("Loading preselector config: " + preselector_config)
    preselector = load_preselector(preselector_config=preselector_config,
        module="its_preselector.web_relay_preselector",
        preselector_class_name = "WebRelayPreselector", sensor_definition={}
    )
    assert preselector is not None