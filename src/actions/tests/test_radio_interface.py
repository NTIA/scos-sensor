""" Test aspects of RadioInterface """

from os.path import join
from actions import usrp


class TestRadioInterface(object):

    mock_scale_factor_dir = './actions/tests/mocks'
    mock_bad_scale_factor_dir = \
        './actions/tests/mocks/scale_factor_files_with_bad_formatting'

    # Create the RadioInterface with the mock usrp_block
    usrp.connect(use_mock_usrp=True)
    if not usrp.is_available:
        raise RuntimeError("Receiver is not available.")
    rx = usrp.radio

    # Ensure the usrp can recover from acquisition errors
    def test_acquisition_errors(self):
        """
            The mock usrp_block will return "bad" data equal to
            the number of times aquire_samples() has been called
            until the reset_bad_acquisitions() has been called
        """
        self.rx.usrp.reset_bad_acquisitions()
        max_retries = 5
        for i in range(max_retries+2):
            try:
                self.rx.acquire_samples(1000, 1000, max_retries)
            except RuntimeError:
                # Check if this was the expected error
                if i == max_retries+1:
                    self.rx.usrp.reset_bad_acquisitions()
                    return
                else:
                    raise RuntimeError(
                        (
                            "RadioInterface failed after {} retries.\r\n" +
                            "Should have failed at {} retries."
                        ).format(i-1, max_retries)
                    )
        # If no error was thrown, this is also an error
        raise RuntimeError(
            "RadioInterface did not throw expected error for\r\n" +
            "failing to retrieve data {} times in a row.".format(max_retries+1)
        )

    def test_tune_result_parsing(self):
        # Use a positive DSP frequency
        f_lo = 1.0e9
        f_dsp = 1.0e6
        self.rx.tune_frequency(f_lo, f_dsp)
        if not (f_lo == self.rx.lo_freq and
                f_dsp == self.rx.dsp_freq):
            raise RuntimeError(
                (
                    "Tune result parsing failed.\r\n" +
                    "Set LO: {}, Parsed LO: {}\r\n" +
                    "Set DSP: {}, Parsed DSP: {}"
                ).format(
                    f_lo, self.rx.lo_freq, f_dsp, self.rx.dsp_freq
                )
            )

        # Use a 0Hz for DSP frequency
        f_lo = 1.0e9
        f_dsp = 0.0
        self.rx.frequency = f_lo
        if not (f_lo == self.rx.lo_freq and
                f_dsp == self.rx.dsp_freq):
            raise RuntimeError(
                (
                    "Tune result parsing failed.\r\n" +
                    "Set LO: {}, Parsed LO: {}\r\n" +
                    "Set DSP: {}, Parsed DSP: {}"
                ).format(
                    f_lo, self.rx.lo_freq, f_dsp, self.rx.dsp_freq
                )
            )

        # Use a nagative DSP frequency
        f_lo = 1.0e9
        f_dsp = -1.0e6
        self.rx.tune_frequency(f_lo, f_dsp)
        if not (f_lo == self.rx.lo_freq and
                f_dsp == self.rx.dsp_freq):
            raise RuntimeError(
                (
                    "Tune result parsing failed.\r\n" +
                    "Set LO: {}, Parsed LO: {}\r\n" +
                    "Set DSP: {}, Parsed DSP: {}"
                ).format(
                    f_lo, self.rx.lo_freq, f_dsp, self.rx.dsp_freq
                )
            )

    def test_load_nonexistent_scale_factor_file(self):
        errored = False
        try:
            self.rx.load_scale_factor_csv('dummy')
        except IOError:
            errored = True
        if not errored:
            raise RuntimeError(
                "Did not throw error when loading nonexistent file."
            )
        return

    def test_poorly_formatted_scale_factor_file(self):
        # Dict of bad scale factor filenames pointing to
        #   their respective errors
        bad_scale_factor_files = {
            'bad_divisions_1.csv': IndexError,
            'bad_divisions_2.csv': IndexError,
            'empty_file.csv': RuntimeError,
            'no_frequencies.csv': RuntimeError,
            'no_gains.csv': RuntimeError,
            'matrix_mismatch.csv': RuntimeError,
            'bad_scale_factor_values.csv': ValueError
        }

        # Test all bad scale factor files for their errors
        for f, err in bad_scale_factor_files.iteritems():
            errored = False
            try:
                self.rx.load_scale_factor_csv(
                    join(self.mock_bad_scale_factor_dir, f)
                )
            except err:
                errored = True
            if not errored:
                raise RuntimeError(
                    (
                        "Did not throw {} when loading bad" +
                        "scale factor file '{}'"
                    ).format(err, f)
                )
        return

    def test_scale_factor_calculation(self):
        """
            Test that the default scale factor is used if not file was loaded.
        """
        self.rx.scale_factors_loaded = False
        self.rx.frequency = 0
        if not (self.rx.scale_factor == self.rx.DEFAULT_SCALE_FACTOR):
            raise RuntimeError(
                "Scale factor did not revert to default.\r\n" +
                "Calculated: {}\r\n".format(self.rx.scale_factor) +
                "Default: {}".format(self.rx.DEFAULT_SCALE_FACTOR)
            )

        """
            Test many scale factor calculations
            sf_test_list = {
                [SF]: (f_lo,gain),
                ...
            }
        """
        sf_test_list = [
            (-7.47813046479, 70e6, 0),  # Outer boundary
            (7.50256094609, 6e9, 0),  # Outer boundary
            (-76.2557869767, 70e6, 76),  # Outer boundary
            (-65.3006507223, 6e9, 76),  # Outer boundary

            (-7.47813046479, 50e6, 0),  # Beyond limits
            (7.50256094609, 7e9, 0),  # Beyond limits
            (-7.47813046479, 70e6, -10),  # Beyond limits
            (-76.2557869767, 70e6, 100),  # Beyond limits

            (-5.40071178476, 1299974999, 0),  # At division
            (-5.41274003389, 1300974999, 0),  # At division
            (0.665475613929, 2199469999, -10),  # At division
            (-76.3832149678, 2200468999, 100),  # At division
            (5.81812380813, 3999124997, -10),  # At division
            (-69.7131434755, 4000123997, 100),  # At division

            (-22.8093940482, 1300000000, 20),  # In division
            (-38.0043597179, 2200000000, 40),  # In division
            (-47.2748864466, 4000000000, 60),  # In division

            (-11.5030015054, 100e6, 5),  # Interpolated
            (-30.0076949404, 600e6, 25),  # Interpolated
            (-18.1326906499, 1200e6, 15),  # Interpolated
            (-71.7994524765, 2000e6, 72),  # Interpolated
            (-32.2959584348, 3000e6, 37),  # Interpolated
            (-51.2041078009, 4100e6, 58),  # Interpolated
            (-11.4556252931, 5000e6, 19),  # Interpolated
        ]

        # Load the mock scale factor file
        self.rx.load_scale_factor_csv(
            join(self.mock_scale_factor_dir, 'mock_scale_factors.csv')
        )

        # Test all cases (rounding to 5 decimals to avoid
        #   floating point errors)
        for (sf, f_lo, g) in sf_test_list:
            self.rx.frequency = f_lo
            self.rx.gain = g
            sf = int(1e5*sf)
            csf = int(1e5*self.rx._get_power_scale_factor())
            if not (sf == csf):
                raise RuntimeError(
                    "Scale factor calculation failed.\r\n" +
                    "Calculated: {}\r\n".format(csf/1e5) +
                    "Expected: {}".format(sf/1e5)
                )

    # Test to ensure the scaled data acquisition is correct
    def test_scaled_acquisition(self):
        # Load the scale factor file
        self.rx.load_scale_factor_csv(
            join(self.mock_scale_factor_dir, 'mock_scale_factors.csv')
        )

        # Do an arbitrary data collection
        self.rx.frequency = 1900e6
        self.rx.gain = 23
        data = self.rx.acquire_samples(1000)

        # Pick an arbitrary sample and round to 5 decimal places
        datum = int(data[236]*1e6)
        true_val = 76415

        # Check the value
        if not (datum == true_val):
            raise RuntimeError(
                "Scale factor not correctly applied to acquisition.\r\n" +
                "Calculated: {}\r\n".format(datum/1e6) +
                "Expected: {}".format(true_val/1e6)
            )
