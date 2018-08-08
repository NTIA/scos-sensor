""" Test aspects of ScaleFactors """

import pytest
from os.path import join
from actions.scale_factor import ScaleFactors


MOCK_SCALE_FACTOR_DIR = './actions/tests/mocks'
MOCK_BAD_SCALE_FACTOR_DIR = \
    './actions/tests/mocks/scale_factor_files_with_bad_formatting'


def test_load_nonexistent_scale_factor_file():
    f = 'dummy'
    msg = "Should raise IOError when loading nonexistent file."
    with pytest.raises(IOError, message=msg):
        sf_file = join(MOCK_SCALE_FACTOR_DIR, f)
        sfs = ScaleFactors(fname=sf_file)  # noqa: F841
    return


def test_poorly_formatted_scale_factor_file():
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
        msg = "Loading '{}' should raise {}".format(f, str(err))
        with pytest.raises(err, message=msg):
            sf_file = join(MOCK_BAD_SCALE_FACTOR_DIR, f)
            sfs = ScaleFactors(fname=sf_file)  # noqa: F841
    return


def test_scale_factor_calculation():
    """
        Test that the default scale factor is used if not file was loaded.
    """
    default_test = 5
    sfs = ScaleFactors(default=default_test)
    csf = sfs.get_scale_factor(0, 0)

    # Assert the algorithm
    msg = "Scale factor did not revert to default.\r\n"
    msg += "Algorithm: {}\r\n".format(csf)
    msg += "Set default: {}".format(default_test)
    assert (csf == default_test), msg

    """
        Test many scale factor calculations
        sf_test_list = [
            (SF, f_lo, gain),
            ...
        ]
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
    sf_name = join(MOCK_SCALE_FACTOR_DIR, 'mock_scale_factors.csv')
    sfs = ScaleFactors(fname=sf_name, default=default_test)

    # Test all cases (rounding to 5 decimals to avoid
    #   floating point errors)
    for (sf, f_lo, g) in sf_test_list:
        osf = sf
        sf = int(1e5*sf)
        csf = int(1e5*sfs.get_power_scale_factor(f_lo, g))

        # Assert the algorithm
        msg = "Scale factor calculation failed.\r\n"
        msg += "Algorithm: {}\r\n".format(csf/1e5)
        msg += "Expected: {}\r\n".format(sf/1e5)
        msg += "Test case: ({}, {}, {})".format(osf, f_lo, g)
        assert (sf == csf), msg
