"""Provides an interface to the on-board GPS."""

import logging
import subprocess
from datetime import datetime
from time import sleep, time

from hardware import radio

logger = logging.getLogger(__name__)


def get_lat_long(timeout_s=1):
    """Use low-level UHD and USRP block methods to sync with GPS."""

    if not radio.is_available:
        return None

    uhd = radio.uhd
    usrp = radio.usrp

    logger.debug("Waiting for GPS lock... ")
    start = time()
    gps_locked = False
    while time() - start < timeout_s and not gps_locked:
        gps_locked = usrp.get_mboard_sensor("gps_locked").to_bool()
        sleep(0.1)

    if not gps_locked:
        logger.warning("Timed out waiting for GPS to lock")
        return None

    logger.debug("GPS locked.")

    if "gpsdo" not in usrp.get_time_sources(0):
        logger.warning("No GPSDO time source detected")
        return None

    usrp.set_time_source("gpsdo")

    if usrp.get_time_source(0) != "gpsdo":
        logger.error("Failed to set GPSDO time source")
        return None

    # Poll get_time_last_pss() until change is seen
    last_t = int(usrp.get_time_last_pps().get_real_secs())
    now_t = int(usrp.get_time_last_pps().get_real_secs())
    while last_t != now_t:
        sleep(0.05)
        now_t = int(usrp.get_time_last_pps().get_real_secs())

    # Then sleep 100ms and set next pps
    sleep(0.1)
    # To use gr-uhd instead of UHD python driver, this line needs to change
    # gps_t = uhd.time_spec_t(usrp.get_mboard_sensor('gps_time').to_int() + 1)
    gps_t = uhd.types.TimeSpec(usrp.get_mboard_sensor("gps_time").to_int() + 1)
    usrp.set_time_next_pps(gps_t)
    dt = datetime.fromtimestamp(gps_t.get_real_secs())
    date_cmd = ["date", "-s", "{:}".format(dt.strftime("%Y/%m/%d %H:%M:%S"))]
    subprocess.check_output(date_cmd, shell=True)
    logger.info("Set USRP and system time to GPS time {}".format(dt.ctime()))

    if "gpsdo" not in usrp.get_clock_sources(0):
        logger.warning("No GPSDO clock source detected")
        return None

    usrp.set_clock_source("gpsdo")

    if usrp.get_clock_source(0) != "gpsdo":
        logger.error("Failed to set GPSDO clock source")
        return None

    start = time()
    ref_locked = False
    while time() - start < timeout_s and not ref_locked:
        ref_locked = usrp.get_mboard_sensor("ref_locked").to_bool()

    if not ref_locked:
        msg = "Timed out waiting for clock to lock to GPSDO reference"
        logger.warning(msg)
        return None

    logger.debug("Clock locked to GPSDO reference")

    try:
        gpgga = usrp.get_mboard_sensor("gps_gpgga").value
        (
            fmt,
            utc,
            lat,
            ns,
            lng,
            ew,
            qual,
            nsats,
            hdil,
            alt,
            altu,
            gdalsep,
            gdalsepu,
            age,
            refid,
        ) = gpgga.split(",")

        latitude = float(lat)
        if ns == "S":
            latitude = -latitude

        latitude_degs = int(latitude / 100)
        latitude_mins = latitude - (latitude_degs * 100)
        latitude_dd = latitude_degs + (latitude_mins / 60)

        longitude = float(lng)
        if ew == "W":
            longitude = -longitude

        longitude_degs = int(longitude / 100)
        longitude_mins = longitude - (longitude_degs * 100)
        longitude_dd = longitude_degs + (longitude_mins / 60)
    except ValueError as err:
        logger.error("Got invalid GPGGA sentence from GPS - {}".format(err))
        return None

    msg = "Updated GPS lat, long ({}, {})".format(latitude_dd, longitude_dd)
    logger.info(msg)

    return (latitude_dd, longitude_dd)
