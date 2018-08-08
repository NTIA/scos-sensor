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

from actions.scale_factor import ScaleFactors

logger = logging.getLogger(__name__)


uhd = None
radio = None
is_available = False


def connect(use_mock_usrp=False):  # -> bool:
    global uhd
    global is_available
    global radio

    logger.warning(use_mock_usrp)

    if not use_mock_usrp:
        try:
            from gnuradio import uhd
        except ImportError:
            logger.warning("gnuradio.uhd not available - disabling radio")
            return False

    try:
        radio_iface = RadioInterface(use_mock_usrp=use_mock_usrp)
        is_available = True
        radio = radio_iface
        return True
    except RuntimeError as err:
        logger.error(err)
        return False


class RadioInterface(object):

    DEFAULT_SCALE_FACTOR = 1

    def __init__(self, sf_file=None, use_mock_usrp=False):
        # Load a mock object is needed
        self.mocked_usrp = use_mock_usrp
        if self.mocked_usrp:
            logger.warning("Using mock USRP.")
            from actions.tests.mocks.usrp_block import UsrpBlockMock
            self.mocked_usrp = True
            self.usrp = UsrpBlockMock()
            self.sf_file = './actions/tests/mocks/mock_scale_factors.csv'
        else:
            if uhd is None:
                err = "UHD not available, did you call connect()?"
                raise RuntimeError(err)

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
            self.usrp = uhd.usrp_source(device_addr=device,
                                        stream_args=stream_args)
            self.sf_file = sf_file

        # Load the scale factors
        self.scale_factors = ScaleFactors(
            fname=self.sf_file,
            default=self.DEFAULT_SCALE_FACTOR
        )
        self.sf = self.DEFAULT_SCALE_FACTOR

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
        # If mocking the usrp_block, work around the uhd
        if self.mocked_usrp:
            tune_result = self.usrp.set_center_freq(freq, dsp_freq)
            logger.debug(tune_result)
        else:
            # Do the tune request normally
            tune_request = uhd.tune_request(freq, dsp_freq)
            tune_result = self.usrp.set_center_freq(tune_request)
            logger.debug(tune_result.to_pp_string())

        # Extract the LO and DSP frequencies
        try:
            """
            Example UHD tune result:
                Tune Result:
                    Target RF  Freq: 73.000000 (MHz)
                    Actual RF  Freq: 73.000000 (MHz)
                    Target DSP Freq: -0.000000 (MHz)
                    Actual DSP Freq: -0.000000 (MHz)

            """
            # Convert the tune result to a string
            tr = str(tune_result)

            # Cut out everything before the actual LO (RF) freq
            lo_start_i = tr.index("Actual RF  Freq:")+17
            tr = tr[lo_start_i:]

            # Retrieve the LO freq string and convert to float
            lo_str = tr[:tr.index(" ")]
            self.lo_freq = float(lo_str)*1e6

            # Cut out everything actual DSP freq
            dsp_start_i = tr.index("Actual DSP Freq:")+17
            tr = tr[dsp_start_i:]

            # Retrieve the DSP freq string and convert to float
            dsp_str = tr[:tr.index(" ")]
            self.dsp_freq = float(dsp_str)*1e6
        except Exception:
            err = "Could not parse SDR tune result."
            raise RuntimeError(err)

        # Request new scale factor
        self.request_scale_factor()

    @property
    def gain(self):  # -> float:
        return self.usrp.get_gain()

    @gain.setter
    def gain(self, gain):
        self.usrp.set_gain(gain)
        logger.debug("set USRP gain: {:.2f} dB".format(self.usrp.get_gain()))
        self.request_scale_factor()

    # Set the scale factor based on USRP gain and LO freq
    def request_scale_factor(self):
        self.sf = self.scale_factors.get_scale_factor(
            lo_frequency=self.lo_freq,
            gain=self.gain
        )

    def acquire_samples(self, n, nskip=1000, retries=5):  # -> np.ndarray:
        """Aquire nskip+n samples and return the last n"""
        o_retries = retries
        while True:
            samples = self.usrp.finite_acquisition(n+nskip)
            data = np.array(samples[nskip:])
            data = data * self.sf
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
