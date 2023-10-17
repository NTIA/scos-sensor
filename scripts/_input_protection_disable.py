import json
from its_preselector.controlbyweb_web_relay import ControlByWebWebRelay
from its_preselector.web_relay_preselector import WebRelayPreselector

sensor_definition_file = "/opt/scos-sensor/configs/sensor_definition.json"
preselector_json_file = "/opt/scos-sensor/configs/preselector_config.json"
spu_relay_json_file = "/opt/scos-sensor/configs/switches/x410_config.json"

# Load Preselector
with open(sensor_definition_file, "r") as f:
    sensor_definition_json = json.load(f)
with open(preselector_json_file, "r") as f:
    preselector_json = json.load(f)
preselector = WebRelayPreselector(sensor_definition_json, preselector_json)

# Load SPU Relay
with open(spu_relay_json_file, "r") as f:
    spu_json = json.load(f)
spu_relay = ControlByWebWebRelay(spu_json)

# Enable Preselector Power
spu_relay.set_state("power_on_preselector")

# Set Preselector to Antenna State
preselector.set_state("antenna")
