from django.conf import settings

import json
import os

ANTENNA_FILE_PATH = os.path.join(settings.REPO_ROOT, "config", "antenna.json")
try:
    with open(ANTENNA_FILE_PATH, "r") as f:
        scos_antenna_obj = json.load(f)
except IOError:
    raise IOError("Unable to open antenna config file at " + ANTENNA_FILE_PATH)

DATA_EXTRACTION_UNIT_PATH = os.path.join(settings.REPO_ROOT, "config",
                                         "data_extraction_unit.json")
try:
    with open(DATA_EXTRACTION_UNIT_PATH, "r") as f:
        data_extract_obj = json.load(f)
except IOError:
    raise IOError("Unable to open data extraction unit config file at " +
                  DATA_EXTRACTION_UNIT_PATH)
