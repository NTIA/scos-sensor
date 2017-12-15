from django.conf import settings

import json
import os

ANTENNA_FILE_PATH = os.path.join(settings.REPO_ROOT, "config", "antenna.json")
try:
    with open(ANTENNA_FILE_PATH, "r") as f:
        scos_antenna_obj = json.load(f)
except IOError:
    raise IOError("Unable to open antenna config file at " + ANTENNA_FILE_PATH)
