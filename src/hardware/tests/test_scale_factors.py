"""Test aspects of ScaleFactors."""

from os import path

import pytest

from hardware import scale_factors
from sensor.settings import REPO_ROOT

RESOURCES_DIR = path.join(REPO_ROOT, "./src/hardware/tests/resources")
TEST_SCALE_FACTORS_FILE = path.join(RESOURCES_DIR, "test_calibration.json")

sfs = scale_factors.load_from_json(TEST_SCALE_FACTORS_FILE)


@pytest.mark.parametrize(
    "sf,f,g",
    [
        # (scale_factor, lo_frequency, gain)
        # Outer boundary
        (-7.47813046479, 70e6, 0),
        (7.50256094609, 6e9, 0),
        (-76.2557869767, 70e6, 76),
        (-65.3006507223, 6e9, 76),
        # Beyond limits
        (-7.47813046479, 50e6, 0),
        (7.50256094609, 7e9, 0),
        (-7.47813046479, 70e6, -10),
        (-76.2557869767, 70e6, 100),
        # At division
        (-5.40071178476, 1299974999, 0),
        (-5.41274003389, 1300974999, 0),
        (0.665475613929, 2199469999, -10),
        (-76.3832149678, 2200468999, 100),
        (5.81812380813, 3999124997, -10),
        (-69.7131434755, 4000123997, 100),
        # In division
        (-22.8093940482, 1300000000, 20),
        (-38.0043597179, 2200000000, 40),
        (-47.2748864466, 4000000000, 60),
        # Interpolated
        (-11.5030015054, 100e6, 5),
        (-30.0076949404, 600e6, 25),
        (-18.1326906499, 1200e6, 15),
        (-71.7994524765, 2000e6, 72),
        (-32.2959584348, 3000e6, 37),
        (-51.2041078009, 4100e6, 58),
        (-11.4556252931, 5000e6, 19),
    ],
)
def test_scale_factor_calculation(sf, f, g):
    """Test that the default scale factor is used if not file was loaded."""

    # Test all cases (rounding to 5 decimals to avoid floating point errors)
    sf = int(1e5 * sf)
    csf = int(1e5 * sfs.get_power_scale_factor(f, g))

    msg = "Scale factor calculation failed.\n"
    msg += "Algorithm: {}\n".format(csf / 1e5)
    msg += "Expected: {}\n".format(sf / 1e5)
    msg += "Test case: ({}, {}, {})".format(sf, f, g)
    assert sf == csf, msg
