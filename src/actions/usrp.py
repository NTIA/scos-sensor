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

import csv


logger = logging.getLogger(__name__)


uhd = None
radio = None
is_available = False


def connect(use_mock_usrp=False):  # -> bool:
    global uhd
    global is_available
    global radio

    if not use_mock_usrp:
        try:
            from gnuradio import uhd
        except ImportError:
            logger.warning("gnuradio.uhd not available - disabling radio")
            return False

    try:
        radio_iface = RadioInterface(use_mock_usrp)
        is_available = True
        radio = radio_iface
        return True
    except RuntimeError as err:
        logger.error(err)
        return False


class RadioInterface(object):

    mocked_usrp = False

    DEFAULT_SCALE_FACTOR = 1
    scale_factor = DEFAULT_SCALE_FACTOR
    scale_factors_loaded = False
    scale_factor_divisions = None
    scale_factor_gains = None
    scale_factor_frequencies = None
    scale_factor_matrix = None

    def __init__(self, use_mock_usrp=False):
        # Load a mock object is needed
        if use_mock_usrp:
            from actions.tests.mocks.mock_usrp_block import mock_usrp_block
            self.mocked_usrp = True
            self.usrp = mock_usrp_block()
            self.usrp.set_auto_dc_offset(True)
            return

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

    def load_scale_factor_csv(self, fname):
        # In case loading is unsuccessful, assume failure
        self.scale_factors_loaded = False

        # Instantiate scale factor arrays/matrix
        self.scale_factor_divisions = []
        self.scale_factor_gains = []
        self.scale_factor_frequencies = []
        self.scale_factor_matrix = []

        # Load data from file
        logger.debug("Loading scale factor data from '{}'".format(fname))
        with open(fname, 'rb') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                # Skip an empty row
                if len(row) < 1:
                    continue
                # Check for a division row
                if row[0] == 'div':
                    try:
                        self.scale_factor_divisions.append([
                            float(row[1]),
                            float(row[2])
                        ])
                    except IndexError:
                        raise IndexError(
                            "Scale factor file improperly formatted.\r\n" +
                            "Divisions need 2 bounds."
                        )
                    continue
                # Check for the list of gains
                if row[0] == '' or row[0] == 'freqs\gains':
                    for i in range(len(row)-1):
                        self.scale_factor_gains.append(
                            float(row[i+1])
                        )
                    continue
                # Must be a frequency row
                self.scale_factor_frequencies.append(float(row[0]))
                self.scale_factor_matrix.append([])
                for i in range(len(row)-1):
                    try:
                        self.scale_factor_matrix[-1].append(float(row[i+1]))
                    except ValueError:
                        raise ValueError(
                            (
                                "Scale factor file improperly formatted.\r\n" +
                                "Invalid scale factor data '{}' at\r\n" +
                                "freq {}Hz in column {}."
                            ).format(
                                str(row[i+1]),
                                self.scale_factor_frequencies[-1],
                                i
                            )
                        )
            f.close()

        # Check that all divisions consist of two values
        for i in range(len(self.scale_factor_divisions)):
            div_len = len(self.scale_factor_divisions[i])
            if not div_len == 2:
                raise RuntimeError(
                    (
                        "Scale factor file improperly formatted.\r\n" +
                        "Division only has {} of 2 required bounds."
                    ).format(div_len)
                )

        # Check that frequency and gain arrays were populated
        if len(self.scale_factor_gains) < 1:
            raise RuntimeError(
                "Scale factor file improperly formatted.\r\n" +
                "No gain values given."
            )
        if len(self.scale_factor_frequencies) < 1:
            raise RuntimeError(
                "Scale factor file improperly formatted.\r\n" +
                "No frequency values given."
            )

        # Check that the number of frequencies matches the SF matrix
        if not len(self.scale_factor_frequencies) == \
                len(self.scale_factor_matrix):
            raise RuntimeError(
                (
                    "Scale factor file improperly formatted.\r\n" +
                    "Number of frequencies ({}) does not match " +
                    "row in SF matrix ({})."
                ).format(
                    len(self.scale_factor_frequencies),
                    len(self.scale_factor_matrix)
                )
            )

        # Check that the number of gains matches the SF matrix
        for i in range(len(self.scale_factor_frequencies)):
            if not len(self.scale_factor_matrix[i]) == \
                    len(self.scale_factor_gains):
                raise RuntimeError(
                    (
                        "Scale factor file improperly formatted.\r\n" +
                        "Number of gains ({}) does not match row in " +
                        "SF matrix ({})\r\nin frequency row {} ({}Hz)."
                    ).format(
                        len(self.scale_factor_gains),
                        len(self.scale_factor_matrix[i]),
                        i,
                        self.scale_factor_frequencies[i]
                    )
                )

        # Sort the data
        (
            self.scale_factor_matrix,
            self.scale_factor_gains,
            self.scale_factor_frequencies
        ) = self.sort_matrix_by_lists(
            self.scale_factor_matrix,
            self.scale_factor_gains,
            self.scale_factor_frequencies
        )

        # Successfully loaded the scale factor file
        self.scale_factors_loaded = True
        return

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
            tr = str(tune_result)
            tr = tr[
                    tr.index("Actual RF  Freq:")+17:
                ]
            self.lo_freq = float(
                    tr[
                        :tr.index(" ")
                    ]
                )*1e6
            tr = tr[
                    tr.index("Actual DSP Freq:")+17:
                ]
            self.dsp_freq = float(
                    tr[
                        :tr.index(" ")
                    ]
                )*1e6
        except Exception:
            raise RuntimeError(
                "Could not parse SDR tune result."
            )
        self.scale_factor = self._get_scale_factor()

    @property
    def gain(self):  # -> float:
        return self.usrp.get_gain()

    @gain.setter
    def gain(self, gain):
        self.usrp.set_gain(gain)
        logger.debug("set USRP gain: {:.2f} dB".format(self.usrp.get_gain()))
        self.scale_factor = self._get_scale_factor()

    # Interpolate to get the power scale factor
    def _get_power_scale_factor(self):
        """
            Find the scale factor closest to the current frequency/gain.
        """

        # Get the LO and gain for the usrp
        f = self.lo_freq
        g = self.gain

        # Get the gain index for the SF interpolation
        g_i = 0
        bypass_gain_interpolation = True
        if g <= self.scale_factor_gains[0]:
            g_i = 0
        elif g >= self.scale_factor_gains[-1]:
            g_i = len(self.scale_factor_gains)-1
        else:
            bypass_gain_interpolation = False
            for i in range(len(self.scale_factor_gains)-1):
                if self.scale_factor_gains[i+1] > g:
                    g_i = i
                    break

        # Get the frequency index range for the SF interpolation
        f_i = 0
        bypass_freq_interpolation = True
        if f <= self.scale_factor_frequencies[0]:
            f_i = 0
        elif f >= self.scale_factor_frequencies[-1]:
            f_i = len(self.scale_factor_frequencies)-1
        else:
            # Narrow the frequency range to a division
            bypass_freq_interpolation = False
            f_div_min = self.scale_factor_frequencies[0]
            f_div_max = self.scale_factor_frequencies[-1]
            for i in range(len(self.scale_factor_divisions)):
                if f >= self.scale_factor_divisions[i][1]:
                    f_div_min = self.scale_factor_divisions[i][1]
                else:
                    # Check if we are in the division
                    if f > self.scale_factor_divisions[i][0]:
                        logger.warning("SDR tuned to within a division:")
                        logger.warning("    LO frequency: {}".format(f))
                        logger.warning("    Division: [{},{}]".format(
                            self.scale_factor_divisions[i][0],
                            self.scale_factor_divisions[i][1]
                        ))
                        logger.warning(
                            "Assumed scale factor of lower boundary.")
                        f_div_min = self.scale_factor_divisions[i][0]
                        f_div_max = self.scale_factor_divisions[i][0]
                        bypass_freq_interpolation = True
                    else:
                        f_div_max = self.scale_factor_divisions[i][0]
                    break
            # Determine the index associated with the frequency/ies
            for i in range(len(self.scale_factor_frequencies)-1):
                if self.scale_factor_frequencies[i] < f_div_min:
                    continue
                if self.scale_factor_frequencies[i+1] > f_div_max:
                    f_i = i
                    break
                if self.scale_factor_frequencies[i+1] > f:
                    f_i = i
                    break

        # Interpolate as needed
        if bypass_gain_interpolation and bypass_freq_interpolation:
            scale_factor = self.scale_factor_matrix[f_i][g_i]
        elif bypass_freq_interpolation:
            scale_factor = self.interpolate_1d(
                g,
                self.scale_factor_gains[g_i],
                self.scale_factor_gains[g_i+1],
                self.scale_factor_matrix[f_i][g_i],
                self.scale_factor_matrix[f_i][g_i+1]
            )
        elif bypass_gain_interpolation:
            scale_factor = self.interpolate_1d(
                f,
                self.scale_factor_frequencies[f_i],
                self.scale_factor_frequencies[f_i+1],
                self.scale_factor_matrix[f_i][g_i],
                self.scale_factor_matrix[f_i+1][g_i]
            )
        else:
            scale_factor = self.interpolate_2d(
                f,
                g,
                self.scale_factor_frequencies[f_i],
                self.scale_factor_frequencies[f_i+1],
                self.scale_factor_gains[g_i],
                self.scale_factor_gains[g_i+1],
                self.scale_factor_matrix[f_i][g_i],
                self.scale_factor_matrix[f_i+1][g_i],
                self.scale_factor_matrix[f_i][g_i+1],
                self.scale_factor_matrix[f_i+1][g_i+1]
            )

        logger.debug("Using power scale factor: {}".format(scale_factor))
        return scale_factor

    # Get the linear scale factor for the current setup
    def _get_scale_factor(self):
        # Ensure scale factors were loaded
        if not self.scale_factors_loaded:
            logger.debug("Defaulting scale factor to: {}".format(
                self.DEFAULT_SCALE_FACTOR
            ))
            return self.DEFAULT_SCALE_FACTOR

        # Get the power scaling factor and convert to linear
        psf = self._get_power_scale_factor()
        sf = (10**(psf/20.0))
        logger.debug("Using linear scale factor: {}".format(sf))
        return sf

    def acquire_samples(self, n, nskip=1000, retries=5):  # -> np.ndarray:
        """Aquire nskip+n samples and return the last n"""
        o_retries = retries
        while True:
            samples = self.usrp.finite_acquisition(n+nskip)
            data = np.array(samples[nskip:])
            data = data * self.scale_factor
            if not len(data) == n:
                if retries > 0:
                    retries = retries - 1
                else:
                    raise RuntimeError(
                        "Failed to acquire correct number of samples " +
                        "{} times in a row.".format(o_retries)
                    )
            else:
                return data

    """
        These are functions which can be moved to a utils file
        since they will or could have more universal applications.
    """
    # Sort a matrix by the list defining its row indeces
    def sort_matrix_by_list(self, m, x):
        for i in range(1, len(x)):
            j = i-1
            m_key = m[i]
            x_key = x[i]
            while (x[j] > x_key) and (j >= 0):
                m[j+1] = m[j]
                x[j+1] = x[j]
                j = j - 1
            m[j+1] = m_key
            x[j+1] = x_key
        return m, x

    # Transpose a matrix
    def transpose_matrix(self, m):
        m_p = []
        for i in range(len(m[0])):
            m_p.append([])
            for j in range(len(m)):
                m_p[i].append(m[j][i])
        return m_p

    # Sort a matrix by two dependent lists defining the indices
    def sort_matrix_by_lists(self, m, x=None, y=None):
        if x is not None:
            m = self.transpose_matrix(m)
            m, x = self.sort_matrix_by_list(m, x)
            m = self.transpose_matrix(m)
        if y is not None:
            m, y = self.sort_matrix_by_list(m, y)
        if x is None and y is not None:
            return m, y
        if x is not None and y is None:
            return m, x
        if x is None and y is None:
            return m
        if x is not None and y is not None:
            return m, x, y

    # Interpolate between points in one dimension
    def interpolate_1d(self, x, x1, x2, y1, y2):
        return y1*(x2-x)/(x2-x1) + y2*(x-x1)/(x2-x1)

    # Interpolate between points in two dimensions
    def interpolate_2d(self, x, y, x1, x2, y1, y2, z11, z21, z12, z22):
        z_y1 = self.interpolate_1d(x, x1, x2, z11, z21)
        z_y2 = self.interpolate_1d(x, x1, x2, z12, z22)
        return self.interpolate_1d(y, y1, y2, z_y1, z_y2)
