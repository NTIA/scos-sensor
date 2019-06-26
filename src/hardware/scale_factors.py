import json
import logging

from collections import OrderedDict

logger = logging.getLogger(__name__)


class ScaleFactors(object):
    def __init__(
        self,
        calibration_datetime,
        calibration_data,
        calibration_frequency_divisions=None,
    ):
        self.calibration_datetime = calibration_datetime
        self.calibration_data = calibration_data
        self.calibration_frequency_divisions = sorted(
            calibration_frequency_divisions,
            key=lambda division: division["lower_bound"],
        )

    # Interpolate to get the power scale factor
    def get_power_scale_factor(self, lo_frequency, gain):
        """Find the scale factor closest to the current frequency/gain."""
        frequencies = sorted(self.calibration_data.keys())

        # Get the LO and gain for the usrp
        f = lo_frequency
        g = gain

        # Get the frequency index range for the SF interpolation
        f_i = 0
        bypass_freq_interpolation = True
        if f <= frequencies[0]:
            f_i = 0
        elif f >= frequencies[-1]:
            f_i = len(frequencies) - 1
        else:
            # Narrow the frequency range to a division
            bypass_freq_interpolation = False
            f_div_min = frequencies[0]
            f_div_max = frequencies[-1]
            for div in self.calibration_frequency_divisions:
                if f >= div["upper_bound"]:
                    f_div_min = div["upper_bound"]
                else:
                    # Check if we are in the division
                    if f > div["lower_bound"]:
                        logger.warning("SDR tuned to within a division:")
                        logger.warning("    LO frequency: {}".format(f))
                        msg = "    Division: [{},{}]"
                        lb = div["lower_bound"]
                        ub = div["upper_bound"]
                        msg = msg.format(lb, ub)
                        logger.warning(msg)
                        msg = "Assumed scale factor of lower boundary."
                        logger.warning(msg)
                        f_div_min = div["lower_bound"]
                        f_div_max = div["lower_bound"]
                        bypass_freq_interpolation = True
                    else:
                        f_div_max = div["lower_bound"]

                    break
            # Determine the index associated with the frequency/ies
            for i in range(len(frequencies) - 1):
                if frequencies[i] < f_div_min:
                    continue
                if frequencies[i + 1] > f_div_max:
                    f_i = i
                    break
                if frequencies[i + 1] > f:
                    f_i = i
                    break

        closest_frequency = frequencies[f_i]
        next_highest_frequency = (
            frequencies[f_i + 1] if f_i + 1 < len(frequencies) else None
        )
        gains = sorted(self.calibration_data[closest_frequency].keys())

        # Get the gain index for the SF interpolation
        g_i = 0
        bypass_gain_interpolation = True
        if g <= gains[0]:
            g_i = 0
        elif g >= gains[-1]:
            g_i = len(gains) - 1
        else:
            bypass_gain_interpolation = False
            for i in range(len(gains) - 1):
                if gains[i + 1] > g:
                    g_i = i
                    break

        closest_gain = gains[g_i]
        next_highest_gain = gains[g_i + 1] if g_i + 1 < len(gains) else None

        # Interpolate as needed
        if bypass_gain_interpolation and bypass_freq_interpolation:
            scale_factor = self.calibration_data[closest_frequency][closest_gain][
                "scale_factor"
            ]
        elif bypass_freq_interpolation:
            scale_factor = self.interpolate_1d(
                g,
                gains[g_i],
                gains[g_i + 1],
                self.calibration_data[closest_frequency][closest_gain]["scale_factor"],
                self.calibration_data[closest_frequency][next_highest_gain][
                    "scale_factor"
                ],
            )
        elif bypass_gain_interpolation:
            scale_factor = self.interpolate_1d(
                f,
                frequencies[f_i],
                frequencies[f_i + 1],
                self.calibration_data[closest_frequency][closest_gain]["scale_factor"],
                self.calibration_data[next_highest_frequency][closest_gain][
                    "scale_factor"
                ],
            )
        else:
            scale_factor = self.interpolate_2d(
                f,
                g,
                frequencies[f_i],
                frequencies[f_i + 1],
                gains[g_i],
                gains[g_i + 1],
                self.calibration_data[closest_frequency][closest_gain]["scale_factor"],
                self.calibration_data[next_highest_frequency][closest_gain][
                    "scale_factor"
                ],
                self.calibration_data[closest_frequency][next_highest_gain][
                    "scale_factor"
                ],
                self.calibration_data[next_highest_frequency][next_highest_gain][
                    "scale_factor"
                ],
            )

        logger.debug("Using power scale factor: {}".format(scale_factor))
        return scale_factor

    def get_scale_factor(self, lo_frequency, gain):
        """Get the linear scale factor for the current setup."""
        psf = self.get_power_scale_factor(lo_frequency, gain)
        sf = 10 ** (psf / 20.0)
        logger.debug("Using linear scale factor: {}".format(sf))
        return sf

    def interpolate_1d(self, x, x1, x2, y1, y2):
        """Interpolate between points in one dimension."""
        return y1 * (x2 - x) / (x2 - x1) + y2 * (x - x1) / (x2 - x1)

    def interpolate_2d(self, x, y, x1, x2, y1, y2, z11, z21, z12, z22):
        """Interpolate between points in two dimensions."""
        z_y1 = self.interpolate_1d(x, x1, x2, z11, z21)
        z_y2 = self.interpolate_1d(x, x1, x2, z12, z22)
        return self.interpolate_1d(y, y1, y2, z_y1, z_y2)


def load_from_json(fname):
    with open(fname) as f:
        sf = json.load(f)

    assert "calibration_datetime" in sf
    assert "calibration_frequency_divisions" in sf
    assert "calibration_points" in sf

    last_frequency = 0
    last_gains = []
    gains = []
    calibration_data = OrderedDict()
    for calibration_point in sf["calibration_points"]:
        frequency = calibration_point["freq_sigan"]
        gain = calibration_point["gain_sigan"]
        if frequency == last_frequency:
            gains.append(gain)
        else:
            calibration_data[frequency] = OrderedDict()
            # gains should be equal for all calibration points
            if last_gains and len(calibration_data) > 2:
                assert gains == last_gains
            last_gains = gains
            gains = [gain]
        last_frequency = frequency
        calibration_data[frequency][gain] = calibration_point

    return ScaleFactors(
        sf["calibration_datetime"],
        calibration_data,
        sf["calibration_frequency_divisions"],
    )
