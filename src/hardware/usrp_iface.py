"""Maintains a persistent connection to the USRP.

Example usage:
    >>> from hardware import usrp_iface
    >>> usrp_iface.connect()
    >>> usrp_iface.is_available
    True
    >>> rx = usrp_iface.radio
    >>> rx.sample_rate = 10e6
    >>> rx.frequency = 700e6
    >>> rx.gain = 40
    >>> samples = rx.acquire_samples(1000)
"""

import logging
from os import path

import numpy as np

from hardware import scale_factors
from hardware.mocks.usrp_block import MockUsrpBlock
from sensor import settings
from sensor.settings import REPO_ROOT

logger = logging.getLogger(__name__)


uhd = None
radio = None
is_available = False

# Testing determined these gain values provide
VALID_GAINS = frozenset([0, 20, 40, 60])


def connect(sf_file=settings.SCALE_FACTORS_FILE):  # -> bool:
    global uhd
    global is_available
    global radio

    if settings.RUNNING_DEMO or settings.RUNNING_TESTS:
        logger.warning("Using mock USRP.")

        usrp = MockUsrpBlock()
        is_available = True
        RESOURCES_DIR = path.join(REPO_ROOT, './src/hardware/tests/resources')
        sf_file = path.join(RESOURCES_DIR, 'test_scale_factors.json')
    else:
        if is_available and radio is not None:
            return True

        try:
            from gnuradio import uhd
        except ImportError:
            logger.warning("gnuradio.uhd not available - disabling radio")
            return False

        search_criteria = uhd.device_addr_t()
        search_criteria['type'] = 'b200'  # ensure this isnt networked usrp
        available_devices = list(uhd.find_devices(search_criteria))
        ndevices_found = len(available_devices)

        if ndevices_found != 1:
            err = "Found {} devices that matches USRP identification\n"
            err += "information in sysinfo:\n"
            err += search_criteria.to_pp_string()
            err += "\nPlease add/correct identifying information."
            err = err.format(ndevices_found)

            for device in available_devices:
                err += "    {}\n".format(device.to_pp_string())

            raise RuntimeError(err)

        device = available_devices[0]
        logger.debug("Using the following USRP:")
        logger.debug(device.to_pp_string())

        stream_args = uhd.stream_args('fc32')
        usrp = uhd.usrp_source(device_addr=device, stream_args=stream_args)

    try:
        radio_iface = RadioInterface(usrp=usrp, sf_file=sf_file)
        is_available = True
        radio = radio_iface
        return True
    except Exception as err:
        logger.exception(err)
        return False


class RadioInterface(object):

    def __init__(self, usrp, sf_file=settings.SCALE_FACTORS_FILE):
        self.usrp = usrp
        self.scale_factor = 1
        try:
            self.scale_factors = scale_factors.load_from_json(sf_file)
        except Exception as err:
            logger.error("Unable to load scale factors, falling back to to 1")
            logger.exception(err)
            self.scale_factors = None

        # Set USRP defaults
        self.usrp.set_auto_dc_offset(True)

    @property
    def sample_rate(self):  # -> float:
        return self.usrp.get_samp_rate()

    @sample_rate.setter
    def sample_rate(self, rate):
        self.usrp.set_samp_rate(rate)
        fs_MHz = self.sample_rate / 1e6
        logger.debug("set USRP sample rate: {:.2f} MS/s".format(fs_MHz))

    @property
    def clock_rate(self):  # -> float:
        return self.usrp.get_clock_rate()

    @clock_rate.setter
    def clock_rate(self, rate):
        self.usrp.set_clock_rate(rate)
        clk_MHz = self.clock_rate / 1e6
        logger.debug("set USRP clock rate: {:.2f} MHz".format(clk_MHz))

    @property
    def frequency(self):  # -> float:
        return self.usrp.get_center_freq()

    @frequency.setter
    def frequency(self, freq):
        self.tune_frequency(freq)

    def tune_frequency(self, freq, dsp_freq=0.0):
        # If mocking the usrp, work around the uhd
        if isinstance(self.usrp, MockUsrpBlock):
            tune_result = self.usrp.set_center_freq(freq, dsp_freq)
            logger.debug(tune_result)
        else:
            tune_request = uhd.tune_request(freq, dsp_freq)
            tune_result = self.usrp.set_center_freq(tune_request)
            logger.debug(tune_result.to_pp_string())

        self.lo_freq = tune_result.actual_rf_freq
        self.dsp_freq = tune_result.actual_dsp_freq

        self.recompute_scale_factor()

    @property
    def gain(self):  # -> float:
        return self.usrp.get_gain()

    @gain.setter
    def gain(self, gain):
        if not gain in VALID_GAINS:
            err = "Requested gain {} not a valid gain. ".format(gain)
            err += "Choose one of {!r}.".format(VALID_GAINS)
            logger.error(err)
            return

        self.usrp.set_gain(gain)
        logger.debug("set USRP gain: {:.1f} dB".format(self.usrp.get_gain()))
        self.recompute_scale_factor()

    def recompute_scale_factor(self):
        """Set the scale factor based on USRP gain and LO freq"""
        if self.scale_factors is None:
            return

        self.scale_factor = self.scale_factors.get_scale_factor(
            lo_frequency=self.lo_freq,
            gain=self.gain
        )

    def acquire_samples(self, n, nskip=200000, retries=5):  # -> np.ndarray:
        """Aquire nskip+n samples and return the last n"""
        o_retries = retries
        while True:
            samples = self.usrp.finite_acquisition(n+nskip)
            data = np.array(samples[nskip:])
            data = data * self.scale_factor
            if not len(data) == n:
                if retries > 0:
                    logger.warning("Acquisition errored.")
                    logger.warning("Retrying {} more times.".format(retries))
                    retries = retries - 1
                else:
                    err = "Failed to acquire correct number of samples "
                    err += "{} times in a row.".format(o_retries)
                    raise RuntimeError(err)
            else:
                return data
