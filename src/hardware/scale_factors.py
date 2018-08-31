import logging

import json
from jsonschema import validate

from sensor.settings import SCALE_FACTORS_SCHEMA_FILE


logger = logging.getLogger(__name__)


class ScaleFactors(object):
    def __init__(self, frequencies, gains, factors, divisions=None):
        self.frequencies = frequencies
        self.gains = gains
        self.factors = factors
        self.divisions = divisions

    # Interpolate to get the power scale factor
    def get_power_scale_factor(self, lo_frequency, gain):
        """Find the scale factor closest to the current frequency/gain."""

        # Get the LO and gain for the usrp
        f = lo_frequency
        g = gain

        # Get the gain index for the SF interpolation
        g_i = 0
        bypass_gain_interpolation = True
        if g <= self.gains[0]:
            g_i = 0
        elif g >= self.gains[-1]:
            g_i = len(self.gains)-1
        else:
            bypass_gain_interpolation = False
            for i in range(len(self.gains)-1):
                if self.gains[i+1] > g:
                    g_i = i
                    break

        # Get the frequency index range for the SF interpolation
        f_i = 0
        bypass_freq_interpolation = True
        if f <= self.frequencies[0]:
            f_i = 0
        elif f >= self.frequencies[-1]:
            f_i = len(self.frequencies)-1
        else:
            # Narrow the frequency range to a division
            bypass_freq_interpolation = False
            f_div_min = self.frequencies[0]
            f_div_max = self.frequencies[-1]
            for div in self.divisions:
                if f >= div['upper_bound']:
                    f_div_min = div['upper_bound']
                else:
                    # Check if we are in the division
                    if f > div['lower_bound']:
                        logger.warning("SDR tuned to within a division:")
                        logger.warning("    LO frequency: {}".format(f))
                        msg = "    Division: [{},{}]"
                        lb = div['lower_bound']
                        ub = div['upper_bound']
                        msg = msg.format(lb, ub)
                        logger.warning(msg)
                        msg = "Assumed scale factor of lower boundary."
                        logger.warning(msg)
                        f_div_min = div['lower_bound']
                        f_div_max = div['lower_bound']
                        bypass_freq_interpolation = True
                    else:
                        f_div_max = div['lower_bound']

                    break
            # Determine the index associated with the frequency/ies
            for i in range(len(self.frequencies)-1):
                if self.frequencies[i] < f_div_min:
                    continue
                if self.frequencies[i+1] > f_div_max:
                    f_i = i
                    break
                if self.frequencies[i+1] > f:
                    f_i = i
                    break

        # Interpolate as needed
        if bypass_gain_interpolation and bypass_freq_interpolation:
            scale_factor = self.factors[f_i][g_i]
        elif bypass_freq_interpolation:
            scale_factor = self.interpolate_1d(
                g,
                self.gains[g_i],
                self.gains[g_i+1],
                self.factors[f_i][g_i],
                self.factors[f_i][g_i+1]
            )
        elif bypass_gain_interpolation:
            scale_factor = self.interpolate_1d(
                f,
                self.frequencies[f_i],
                self.frequencies[f_i+1],
                self.factors[f_i][g_i],
                self.factors[f_i+1][g_i]
            )
        else:
            scale_factor = self.interpolate_2d(
                f,
                g,
                self.frequencies[f_i],
                self.frequencies[f_i+1],
                self.gains[g_i],
                self.gains[g_i+1],
                self.factors[f_i][g_i],
                self.factors[f_i+1][g_i],
                self.factors[f_i][g_i+1],
                self.factors[f_i+1][g_i+1]
            )

        logger.debug("Using power scale factor: {}".format(scale_factor))
        return scale_factor

    def get_scale_factor(self, lo_frequency, gain):
        """Get the linear scale factor for the current setup."""
        psf = self.get_power_scale_factor(lo_frequency, gain)
        sf = 10**(psf/20.0)
        logger.debug("Using linear scale factor: {}".format(sf))
        return sf

    def interpolate_1d(self, x, x1, x2, y1, y2):
        """Interpolate between points in one dimension."""
        return y1*(x2-x)/(x2-x1) + y2*(x-x1)/(x2-x1)

    def interpolate_2d(self, x, y, x1, x2, y1, y2, z11, z21, z12, z22):
        """Interpolate between points in two dimensions."""
        z_y1 = self.interpolate_1d(x, x1, x2, z11, z21)
        z_y2 = self.interpolate_1d(x, x1, x2, z12, z22)
        return self.interpolate_1d(y, y1, y2, z_y1, z_y2)


def load_from_json(fname):
    """Validate JSON file against schema and initialize ScaleFactors."""

    with open(SCALE_FACTORS_SCHEMA_FILE) as f:
        schema = json.load(f)

    with open(fname) as f:
        sf = json.load(f)

    # Raises jsonschema.exceptions.ValidationError if invalid
    validate(sf, schema)

    # Dimensions of the factors array is not validated by the schema
    factor_rows = len(sf['factors'])
    nfrequencies = len(sf['frequencies'])
    ngains = len(sf['gains'])

    msg = "Number of rows in factors 2D array ({}) ".format(factor_rows)
    msg += "not equal to number of frequencies ({})".format(nfrequencies)
    assert len(sf['factors']) == len(sf['frequencies']), msg

    msg = "factors row {!r} isn't the same length as the `gains` array ({})"
    for row in sf['factors']:
        assert len(row) == ngains, format(row, ngains)

    # Ensure frequencies and gains arrays are already sorted

    assert sf['frequencies'] == sorted(sf['frequencies']), "freqs not sorted"
    assert sf['gains'] == sorted(sf['gains']), "gains not sorted"

    return ScaleFactors(**sf)
