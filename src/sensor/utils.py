import json
import logging
import os
import shutil
from datetime import datetime

from django.conf import settings

logger = logging.getLogger(__name__)


def get_datetime_from_timestamp(ts):
    return datetime.fromtimestamp(ts)


def get_timestamp_from_datetime(dt: datetime):
    """Assumes UTC datetime."""
    return int(dt.timestamp())


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
