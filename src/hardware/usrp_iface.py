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

from hardware import calibration
from hardware.mocks.usrp_block import MockUsrp
from sensor import settings
from sensor.settings import REPO_ROOT

logger = logging.getLogger(__name__)

uhd = None
radio = None
is_available = False

# Testing determined these gain values provide a good mix of sensitivity and
# dynamic range performance
VALID_GAINS = (0, 20, 40, 60)


def connect(
    sensor_cal_file=settings.SENSOR_CALIBRATION_FILE,
    sigan_cal_file=settings.SIGAN_CALIBRATION_FILE,
):  # -> bool:
    global uhd
    global is_available
    global radio

    if settings.MOCK_RADIO:
        logger.warning("Using mock USRP.")
        random = settings.MOCK_RADIO_RANDOM
        usrp = MockUsrp(randomize_values=random)
        is_available = True
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
        radio_iface = RadioInterface(
            usrp=usrp, sensor_cal_file=sensor_cal_file, sigan_cal_file=sigan_cal_file
        )
        is_available = True
        radio = radio_iface
        return True
    except Exception as err:
        logger.exception(err)
        return False


class RadioInterface(object):

    # Define the default calibration dicts
    DEFAULT_SIGAN_CALIBRATION = {
        "gain_sigan": None,  # Defaults to gain setting
        "enbw_sigan": None,  # Defaults to sample rate
        "noise_figure_sigan": 0,
        "1db_compression_sigan": 100,
    }
    DEFAULT_SENSOR_CALIBRATION = {
        "gain_sensor": None,  # Defaults to sigan gain
        "enbw_sensor": None,  # Defaults to sigan enbw
        "noise_figure_sensor": None,  # Defaults to sigan noise figure
        "1db_compression_sensor": None,  # Defaults to sigan compression + preselector gain
        "gain_preselector": 0,
        "noise_figure_preselector": 0,
        "1db_compression_preselector": 100,
    }

    # Define thresholds for determining ADC overload for the sigan
    ADC_FULL_RANGE_THRESHOLD = 0.98  # ADC scale -1<sample<1, magnitude threshold = 0.98
    ADC_OVERLOAD_THRESHOLD = (
        0.01
    )  # Ratio of samples above the ADC full range to trigger overload

    def __init__(
        self,
        usrp,
        sensor_cal_file=settings.SENSOR_CALIBRATION_FILE,
        sigan_cal_file=settings.SIGAN_CALIBRATION_FILE,
    ):
        self.usrp = usrp

        # Set the default calibration values
        self.sensor_calibration_data = self.DEFAULT_SENSOR_CALIBRATION.copy()
        self.sigan_calibration_data = self.DEFAULT_SIGAN_CALIBRATION.copy()

        # Try and load sensor/sigan calibration data
        if not settings.MOCK_RADIO:
            try:
                self.sensor_calibration = calibration.load_from_json(sensor_cal_file)
            except Exception as err:
                logger.error(
                    "Unable to load sensor calibration data, reverting to none"
                )
                logger.exception(err)
                self.sensor_calibration = None
            try:
                self.sigan_calibration = calibration.load_from_json(sigan_cal_file)
            except Exception as err:
                logger.error("Unable to load sigan calibration data, reverting to none")
                logger.exception(err)
                self.sigan_calibration = None
        else:  # If in testing, create our own test files
            import hardware.tests.resources.utils as test_utils

            dummy_calibration = test_utils.create_dummy_calibration()
            self.sensor_calibration = dummy_calibration
            self.sigan_calibration = dummy_calibration

    @property
    def sample_rate(self):  # -> float:
        return self.usrp.get_rx_rate()

    @sample_rate.setter
    def sample_rate(self, rate):
        """Sets the sample_rate and the clock_rate based on the sample_rate"""
        self.usrp.set_rx_rate(rate)
        fs_MHz = self.sample_rate / 1e6
        logger.debug("set USRP sample rate: {:.2f} MS/s".format(fs_MHz))
        # Set the clock rate based on calibration
        if self.sigan_calibration is not None:
            clock_rate = self.sigan_calibration.get_clock_rate(rate)
        else:
            clock_rate = self.sample_rate
            # Maximize clock rate while keeping it under 40e6
            while clock_rate <= 40e6:
                clock_rate *= 2
            clock_rate /= 2
        self.clock_rate = clock_rate

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

    def recompute_calibration_data(self):
        """Set the calibration data based on the currently tuning"""

        # Try and get the sensor calibration data
        if self.sensor_calibration is not None:
            self.sensor_calibration_data.update(
                self.sensor_calibration.get_calibration_dict(
                    sample_rate=self.sample_rate,
                    lo_frequency=self.frequency,
                    gain=self.gain,
                )
            )
        else:
            self.sensor_calibration_data = self.DEFAULT_SENSOR_CALIBRATION.copy()

        # Try and get the sigan calibration data
        if self.sigan_calibration is not None:
            self.sigan_calibration_data.update(
                self.sigan_calibration.get_calibration_dict(
                    sample_rate=self.sample_rate,
                    lo_frequency=self.frequency,
                    gain=self.gain,
                )
            )
        else:
            self.sigan_calibration_data = self.DEFAULT_SIGAN_CALIBRATION.copy()

        # Catch any defaulting calibration values for the sigan
        if self.sigan_calibration_data["gain_sigan"] is None:
            self.sigan_calibration_data["gain_sigan"] = self.gain
        if self.sigan_calibration_data["enbw_sigan"] is None:
            self.sigan_calibration_data["enbw_sigan"] = self.sample_rate

        # Catch any defaulting calibration values for the sensor
        if self.sensor_calibration_data["gain_sensor"] is None:
            self.sensor_calibration_data["gain_sensor"] = self.sigan_calibration_data[
                "gain_sigan"
            ]
        if self.sensor_calibration_data["enbw_sensor"] is None:
            self.sensor_calibration_data["enbw_sensor"] = self.sigan_calibration_data[
                "enbw_sigan"
            ]
        if self.sensor_calibration_data["noise_figure_sensor"] is None:
            self.sensor_calibration_data[
                "noise_figure_sensor"
            ] = self.sigan_calibration_data["noise_figure_sigan"]
        if self.sensor_calibration_data["1db_compression_sensor"] is None:
            self.sensor_calibration_data["1db_compression_sensor"] = (
                self.sensor_calibration_data["gain_preselector"]
                + self.sigan_calibration_data["1db_compression_sigan"]
            )

    def create_calibration_annotation(self):
        annotation_md = {
            "ntia-core:annotation_type": "CalibrationAnnotation",
            "ntia-sensor:gain_sigan": self.sigan_calibration_data["gain_sigan"],
            "ntia-sensor:noise_figure_sigan": self.sigan_calibration_data[
                "noise_figure_sigan"
            ],
            "ntia-sensor:1db_compression_point_sigan": self.sigan_calibration_data[
                "1db_compression_sigan"
            ],
            "ntia-sensor:enbw_sigan": self.sigan_calibration_data["enbw_sigan"],
            "ntia-sensor:gain_preselector": self.sensor_calibration_data[
                "gain_preselector"
            ],
            "ntia-sensor:noise_figure_sensor": self.sensor_calibration_data[
                "noise_figure_sensor"
            ],
            "ntia-sensor:1db_compression_point_sensor": self.sensor_calibration_data[
                "1db_compression_sensor"
            ],
            "ntia-sensor:enbw_sensor": self.sensor_calibration_data["enbw_sensor"],
            "ntia-sensor:mean_noise_power_sensor": "",
        }
        return annotation_md

    def acquire_samples(self, n, nskip=0, retries=5):  # -> np.ndarray:
        """Aquire nskip+n samples and return the last n"""

        # Get the calibration data for the acquisition
        self.recompute_calibration_data()

        # Compute the linear gain
        db_gain = self.sensor_calibration_data["gain_sensor"]
        linear_gain = 10 ** (db_gain / 20.0)

        # Try to acquire the samples
        max_retries = retries
        while True:
            # No need to skip initial samples when simulating the radio
            if settings.MOCK_RADIO:
                nsamps = n
            else:
                nsamps = n + nskip

            samples = self.usrp.recv_num_samps(
                nsamps,  # number of samples
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

            if not settings.MOCK_RADIO:
                data = data[nskip:]

            if not len(data) == n:
                if retries > 0:
                    msg = "USRP error: requested {} samples, but got {}."
                    logger.warning(msg.format(n + nskip, data_len))
                    logger.warning("Retrying {} more times.".format(retries))
                    retries = retries - 1
                else:
                    err = "Failed to acquire correct number of samples "
                    err += "{} times in a row.".format(max_retries)
                    raise RuntimeError(err)
            else:
                logger.debug("Successfully acquired {} samples.".format(n))

                # Check IQ values versus ADC max for sigan compression
                self.sigan_overload = False
                i_samples = np.abs(np.real(data))
                q_samples = np.abs(np.imag(data))
                i_over_threshold = np.sum(i_samples > self.ADC_FULL_RANGE_THRESHOLD)
                q_over_threshold = np.sum(q_samples > self.ADC_FULL_RANGE_THRESHOLD)
                total_over_threshold = i_over_threshold + q_over_threshold
                ratio_over_threshold = float(total_over_threshold) / n
                if ratio_over_threshold > self.ADC_OVERLOAD_THRESHOLD:
                    self.sigan_overload = True

                # Scale the data back to RF power and return it
                data /= linear_gain
                return data
