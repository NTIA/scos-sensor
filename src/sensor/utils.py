import json
import logging
import os
import shutil
from datetime import datetime

import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)


class FindNearestDict(dict):
    """Return associated value for nearest matching key.

    Raises TypeError if key is not a real number.

    Example usage;
        >>> cals = {100e6: 1.1, 200e6: 1.2, 500e6: 1.5}
        >>> nearest_cal = FindNearestDict(cals)
        >>> nearest_cal[100e6]
        1.1
        >>> nearest_cal[300e6]
        1.2
        >>> nearest_cal[400e6]
        1.5
    """

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._check_keys(self.keys())

    @staticmethod
    def _check_keys(keys):
        if not np.all(np.isreal(keys)):
            raise TypeError("Caught non-real key")

    def _find_nearest(self, value):
        """Find the index of the closest matching value in a NumPy array."""
        float_keys = np.array(self.keys(), dtype=float)
        # http://stackoverflow.com/a/2566508
        nearest_idx = np.abs(float_keys - value).argmin()
        return self.get(float_keys[nearest_idx])

    def __getitem__(self, item):
        """Override __getitem__ to find nearest"""
        self._check_keys(item)
        return self._find_nearest(item)

    def __setitem__(self, item, value):
        self._check_keys(item)
        dict.__setitem__(self, item, value)

    def update(self, newdict):
        self._check_keys(newdict.keys())
        dict.update(self, newdict)


def get_datetime_from_timestamp(ts):
    return datetime.fromtimestamp(ts)


def get_timestamp_from_datetime(dt):
    """Assumes UTC datetime."""
    return int(dt.strftime("%s"))


def parse_datetime_str(d):
    return datetime.strptime(d, settings.DATETIME_FORMAT)


def copy_driver_files():
    """Copy driver files where they need to go"""
    for root, dirs, files in os.walk(settings.DRIVERS_DIR):
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
                            settings.DRIVERS_DIR, scos_file["source_path"]
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
