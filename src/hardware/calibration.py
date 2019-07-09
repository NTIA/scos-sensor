import json
import logging

logger = logging.getLogger(__name__)


class Calibration(object):
    def __init__(
        self,
        calibration_datetime,
        calibration_data,
        clock_rate_lookup_by_sample_rate,
        calibration_frequency_divisions=None,
    ):
        self.calibration_datetime = calibration_datetime
        self.calibration_data = calibration_data
        self.clock_rate_lookup_by_sample_rate = clock_rate_lookup_by_sample_rate
        self.calibration_frequency_divisions = sorted(
            calibration_frequency_divisions,
            key=lambda division: division["lower_bound"],
        )

    def get_clock_rate(self, sample_rate):
        """Find the clock rate (Hz) using the given sample_rate (samples per second)"""
        for mapping in self.clock_rate_lookup_by_sample_rate:
            if mapping["sample_rate"] == sample_rate:
                return mapping["clock_frequency"]
        return sample_rate

    # Interpolate to get the power scale factor
    def get_power_scale_factor(self, sample_rate, lo_frequency, gain):
        """Find the scale factor closest to the current frequency/gain."""
        
        # Check if the sample rate was calibrated
        sr = sample_rate
        srs = sorted(self.calibration_data.keys())
        if sr not in srs:
            logger.warning("Requested sample rate was not calibrated!")
            logger.warning("Assuming default sample rate:")
            logger.warning("    Requested sample rate: {}".format(sr))
            logger.warning("    Assumed sample rate:   {}".format(sr[0]))
            sr = sr[0]
        
        # Get the nearest calibrated frequency and its index
        f = lo_frequency
        fs = sorted(self.calibration_data[sr].keys())
        f_i = -1
        bypass_freq_interpolation = True
        if f < fs[0]: # Frequency below calibrated range
            f_i = 0
            logger.warning("Tuned frequency is below calibrated range!")
            logger.warning("Assuming lowest frequency:")
            logger.warning("    Tuned frequency:   {}".format(f))
            logger.warning("    Assumed frequency: {}".format(fs[f_i]))
        elif f > fs[-1]: # Frequency above calibrated range
            f_i = len(fs)-1
            logger.warning("Tuned frequency is above calibrated range!")
            logger.warning("Assuming highest frequency:")
            logger.warning("    Tuned frequency:   {}".format(f))
            logger.warning("    Assumed frequency: {}".format(fs[f_i]))
        else:
            # Ensure we use frequency interpolation
            bypass_freq_interpolation = False
            # Check if we are within a frequency division
            for div in self.calibration_frequency_divisions:
                if f > div['lower_bound'] and f < div['upper_bound']:
                    logger.warning("Tuned frequency within a division!")
                    logger.warning("Assuming frequency at lower bound:")
                    logger.warning("    Tuned frequency:   {}".format(f))
                    logger.warning("    Lower bound:       {}".format(div['lower_bound']))
                    logger.warning("    Upper bound:       {}".format(div['upper_bound']))
                    logger.warning("    Assumed frequency: {}".format(div['lower_bound']))
                    f = div['lower_bound'] # Interpolation will force this point; no interpolation error
            # Determine the index associated with the closest frequency less than or equal to f
            for i in range(len(fs)-1):
                f_i = i
                # If the next frequency is larger, we're done
                if fs[i+1] > f:
                    break
        
        # Get the nearest calibrated gain and its index
        g = gain
        gs = sorted(self.calibration_data[sr][fs[f_i]].keys())
        g_i = -1
        g_fudge = 0
        bypass_gain_interpolation = True
        if g < gs[0]: # Gain below calibrated range
            g_i = 0
            g_fudge = gs[0]-g
            logger.warning("Current gain is below calibrated range!")
            logger.warning("Assuming lowest gain and extending:")
            logger.warning("    Current gain: {}".format(g))
            logger.warning("    Assumed gain: {}".format(gs[0]))
            logger.warning("    Fudge factor: {}".format(g_fudge))
        elif g > gs[-1]: # Gain above calibrated range
            g_i = len(gs)-1
            g_fudge = gs[-1]-g
            logger.warning("Current gain is above calibrated range!")
            logger.warning("Assuming lowest gain and extending:")
            logger.warning("    Current gain: {}".format(g))
            logger.warning("    Assumed gain: {}".format(gs[-1]))
            logger.warning("    Fudge factor: {}".format(g_fudge))
        else:
            # Ensure we use gain interpolation
            bypass_gain_interpolation = False
            # Determine the index associated with the closest gain less than or equal to g
            for i in range(len(gs)-1):
                g_i = i
                # If the next gain is larger, we're done
                if gs[i+1] > g:
                    break

        # Interpolate as needed
        if bypass_gain_interpolation and bypass_freq_interpolation:
            scale_factor = self.calibration_data[sr][fs[f_i]][gs[g_i]][
                "scale_factor"
            ]
        elif bypass_freq_interpolation:
            scale_factor = self.interpolate_1d(
                g,
                gs[g_i],
                gs[g_i+1],
                self.calibration_data[sr][fs[f_i]][gs[g_i]]["scale_factor"],
                self.calibration_data[sr][fs[f_i]][gs[g_i+1]]["scale_factor"]
            )
        elif bypass_gain_interpolation:
            scale_factor = self.interpolate_1d(
                f,
                fs[f_i],
                fs[f_i+1],
                self.calibration_data[sr][fs[f_i]][gs[g_i]]["scale_factor"],
                self.calibration_data[sr][fs[f_i+1]][gs[g_i]]["scale_factor"]
            )
        else:
            scale_factor = self.interpolate_2d(
                f,
                g,
                fs[f_i],
                fs[f_i+1],
                gs[g_i],
                gs[g_i+1],
                self.calibration_data[sr][fs[f_i]][gs[g_i]]["scale_factor"],
                self.calibration_data[sr][fs[f_i+1]][gs[g_i]]["scale_factor"],
                self.calibration_data[sr][fs[f_i]][gs[g_i+1]]["scale_factor"],
                self.calibration_data[sr][fs[f_i+1]][gs[g_i+1]]["scale_factor"]
            )
        
        # Apply the gain fudge factor if needed
        scale_factor += g_fudge

        logger.debug("Using power scale factor: {}".format(scale_factor))
        return scale_factor

    def get_scale_factor(self, sample_frequency, lo_frequency, gain):
        """Get the linear scale factor for the current setup."""
        psf = self.get_power_scale_factor(sample_frequency, lo_frequency, gain)
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
    with open(fname) as file:
        calibration = json.load(file)

    assert "calibration_datetime" in calibration
    assert "calibration_frequency_divisions" in calibration
    assert "calibration_points" in calibration
    assert "clock_rate_lookup_by_sample_rate" in calibration

    calibration_data = {}
    for calibration_point in calibration["calibration_points"]:
        # Get the dictionary keys
        frequency = calibration_point["freq_sigan"]
        gain = calibration_point["gain_sigan"]
        #sample_rate = calibration_point['sample_rate_sigan']
        sample_rate = 1 #Debug until sample rate is added to cal file

        # Ensure the dictionary is fleshed out
        if sample_rate not in calibration_data.keys():
            calibration_data[sample_rate] = {}
        if frequency not in calibration_data[sample_rate].keys():
            calibration_data[sample_rate][frequency] = {}
        
        # Add the calibration point
        calibration_data[sample_rate][frequency][gain] = calibration_point

    return Calibration(
        calibration["calibration_datetime"],
        calibration_data,
        calibration["clock_rate_lookup_by_sample_rate"],
        calibration["calibration_frequency_divisions"],
    )
