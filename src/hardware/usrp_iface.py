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
from hardware.mocks.usrp_block import MockUsrp
from sensor import settings
from sensor.settings import REPO_ROOT

logger = logging.getLogger(__name__)

uhd = None
radio = None
is_available = False

# Testing determined these gain values provide
VALID_GAINS = (0, 20, 40, 60)


def connect(sf_file=settings.SCALE_FACTORS_FILE):  # -> bool:
    global uhd
    global is_available
    global radio

    if settings.RUNNING_DEMO or settings.RUNNING_TESTS or settings.MOCK_RADIO:
        logger.warning("Using mock USRP.")
        random = settings.MOCK_RADIO_RANDOM
        usrp = MockUsrp(randomize_values=random)
        is_available = True
        RESOURCES_DIR = path.join(REPO_ROOT, "./src/hardware/tests/resources")
        sf_file = path.join(RESOURCES_DIR, "test_scale_factors.json")
    else:
        if is_available and radio is not None:
            return True

        try:
            import uhd
        except ImportError:
            logger.warning("uhd not available - disabling radio")
            return False

        usrp_args = "type=b200"  # find any b-series device

        try:
            usrp = uhd.usrp.MultiUSRP(usrp_args)
        except RuntimeError:
            err = "No device found matching search parameters {!r}\n"
            err = err.format(usrp_args)
            raise RuntimeError(err)

        logger.debug("Using the following USRP:")
        logger.debug(usrp.get_pp_string())

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

    @property
    def sample_rate(self):  # -> float:
        return self.usrp.get_rx_rate()

    @sample_rate.setter
    def sample_rate(self, rate):
        self.usrp.set_rx_rate(rate)
        fs_MHz = self.sample_rate / 1e6
        logger.debug("set USRP sample rate: {:.2f} MS/s".format(fs_MHz))

    @property
    def clock_rate(self):  # -> float:
        return self.usrp.get_master_clock_rate()

    @clock_rate.setter
    def clock_rate(self, rate):
        self.usrp.set_master_clock_rate(rate)
        clk_MHz = self.clock_rate / 1e6
        logger.debug("set USRP clock rate: {:.2f} MHz".format(clk_MHz))

    @property
    def frequency(self):  # -> float:
        return self.usrp.get_rx_freq()

    @frequency.setter
    def frequency(self, freq):
        self.tune_frequency(freq)
        self.recompute_scale_factor()

    def tune_frequency(self, rf_freq, dsp_freq=0):
        if isinstance(self.usrp, MockUsrp):
            tune_result = self.usrp.set_rx_freq(rf_freq, dsp_freq)
            logger.debug(tune_result)
        else:
            tune_request = uhd.types.TuneRequest(rf_freq, dsp_freq)
            tune_result = self.usrp.set_rx_freq(tune_request)
            # FIXME: report actual values when available - see note below
            msg = "rf_freq: {}, dsp_freq: {}"
            logger.debug(msg.format(rf_freq, dsp_freq))

        # FIXME: uhd.types.TuneResult doesn't seem to be implemented
        #        as of uhd 3.13.1.0-rc1
        #        Fake it til they make it
        # self.lo_freq = tune_result.actual_rf_freq
        # self.dsp_freq = tune_result.actual_dsp_freq
        self.lo_freq = rf_freq
        self.dsp_freq = dsp_freq

    @property
    def gain(self):  # -> float:
        return self.usrp.get_rx_gain()

    @gain.setter
    def gain(self, gain):
        if gain not in VALID_GAINS:
            err = "Requested invalid gain {}. ".format(gain)
            err += "Choose one of {!r}.".format(VALID_GAINS)
            logger.error(err)
            return

        self.usrp.set_rx_gain(gain)
        msg = "set USRP gain: {:.1f} dB"
        logger.debug(msg.format(self.usrp.get_rx_gain()))
        self.recompute_scale_factor()

    def recompute_scale_factor(self):
        """Set the scale factor based on USRP gain and LO freq"""
        if self.scale_factors is None:
            return

        self.scale_factor = self.scale_factors.get_scale_factor(
            lo_frequency=self.frequency, gain=self.gain
        )

    def acquire_samples(self, n, nskip=200000, retries=5):  # -> np.ndarray:
        """Aquire nskip+n samples and return the last n"""
        o_retries = retries
        while True:
            samples = self.usrp.recv_num_samps(
                n + nskip,  # number of samples
                self.frequency,  # center frequency in Hz
                self.sample_rate,  # sample rate in samples per second
                [0],  # channel list
                self.gain,  # gain in dB
            )
            # usrp.recv_num_samps returns a numpy array of shape
            # (n_channels, n_samples) and dtype complex64
            assert samples.dtype == np.complex64
            assert len(samples.shape) == 2 and samples.shape[0] == 1
            data = samples[0]  # isolate data for channel 0
            data_len = len(data)
            data = data[nskip:]
            data = data * self.scale_factor
            if not len(data) == n:
                if retries > 0:
                    msg = "USRP error: requested {} samples, but got {}."
                    logger.warning(msg.format(n + nskip, data_len))
                    logger.warning("Retrying {} more times.".format(retries))
                    retries = retries - 1
                else:
                    err = "Failed to acquire correct number of samples "
                    err += "{} times in a row.".format(o_retries)
                    raise RuntimeError(err)
            else:
                logger.debug("Successfully acquired {} samples.".format(n))
                return data
