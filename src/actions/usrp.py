"""Maintains a persistent connection to the USRP.

Example usage:
    >>> from actions import usrp
    >>> usrp.connect(config.RADIO_ID)
    >>> usrp.is_available
    True
    >>> rx = usrp.radio
    >>> rx.sample_rate = 10e6
    >>> rx.frequency = 700e6
    >>> rx.gain = 30
    >>> samples = rx.acquire_samples(1000)
"""

import logging

import numpy as np

from capabilities.models import SensorDefinition

from .utils import FindNearestDict


logger = logging.getLogger(__name__)


uhd = None
radio = None
is_available = False


def connect():  # -> bool:
    global uhd
    global is_available
    global radio

    try:
        from gnuradio import uhd
    except ImportError:
        logger.warning("gnuradio.uhd not available - disabling radio")
        return False

    try:
        radio_iface = RadioInterface()
        is_available = True
        radio = radio_iface
        return True
    except RuntimeError as err:
        logger.error(err)
        return False


class RadioInterface(object):
    def __init__(self):
        if uhd is None:
            raise RuntimeError("UHD not available, did you call connect()?")

        search_criteria = uhd.device_addr_t()
        search_criteria['type'] = 'b200'  # ensure we don't find networked usrp
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
        self.usrp = uhd.usrp_source(device_addr=device,
                                    stream_args=stream_args)

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
        tune_request = uhd.tune_request(freq)
        tune_result = self.usrp.set_center_freq(tune_request)
        logger.debug(tune_result.to_pp_string())

    @property
    def gain(self):  # -> float:
        return self.usrp.get_gain()

    @gain.setter
    def gain(self, gain):
        self.usrp.set_gain(gain)
        logger.debug("set USRP gain: {:.2f} dB".format(self.usrp.get_gain()))

    def _get_scale_factor(self):
        """Find the scale factor closest to the current frequency.

        If no sensor definition exists or no scale factors are set, return 1.

        """
        default = 1

        try:
            sensor_def = SensorDefinition.objects.get()
        except SensorDefinition.DoesNotExist:
            msg = "No sensor definition exists, using default scale factor"
            logger.debug(msg)
            return default

        scale_factors = sensor_def.receiver.scale_factors.values()
        nearest_factor_map = FindNearestDict(
            (sf['frequency'], sf['scale_factor']) for sf in scale_factors
        )

        try:
            scale_factor = nearest_factor_map[self.frequency]
        except ValueError:
            logger.debug("No scale factors set, using default scale factor")
            return default

        logger.debug("Using scale factor {}".format(scale_factor))
        return scale_factor

    def acquire_samples(self, n, nskip=1000):  # -> np.ndarray:
        """Aquire nskip+n samples and return the last n"""
        total_samples = nskip + n
        acquired_samples = self.usrp.finite_acquisition(total_samples)
        scale_factor = self._get_scale_factor()
        data = np.array(acquired_samples[nskip:]) * scale_factor
        nreceived = len(data)
        if nreceived != n:
            err = "Requested {} samples, but received {}"
            raise RuntimeError(err.format(n, nreceived))

        return data
