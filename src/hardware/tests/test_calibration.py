"""Test aspects of ScaleFactors."""

import datetime
import json
import random
from os import path

import pytest

from hardware import calibration


class TestCalibrationFile:
    # Ensure we load the test file
    setup_complete = False

    """ Function to create the easily interpolated scale factor """

    def easy_sf(self, sr, f, g):
        return (-1 * g) + (sr / 1e6) + (f / 1e9)

    """ Get a random index from a list """

    def rand_index(self, l):
        return random.randint(0, len(l) - 1)

    """ Check if a set of points is a duplicate """

    def check_duplicate(self, sr, f, g):
        for pt in self.pytest_points:
            duplicate_f = f == pt["frequency"]
            duplicate_g = g == pt["gain"]
            duplicate_sr = sr == pt["sample_rate"]
            if duplicate_f and duplicate_g and duplicate_sr:
                return True

    """ Handle floating point comparison """

    def is_close(self, a, b, tolerance):
        return abs(a - b) <= tolerance

    """ Test a the calculated value against the algorithm """

    def run_pytest_point(self, sr, f, g, reason, sr_m=False, f_m=False, g_m=False):
        # Check that the setup was completed
        assert self.setup_complete, "Setup was not completed"

        # If this point was tested before, skip it (triggering a new one)
        if self.check_duplicate(sr, f, g):
            return False

        # If the point doesn't have modified inputs, use the algorithm ones
        if not f_m:
            f_m = f
        if not g_m:
            g_m = g
        if not sr_m:
            sr_m = sr

        # Calculate what the scale factor should be
        sf = self.easy_sf(sr_m, f_m, g_m)

        # Get the scale factor from the algorithm
        csf = self.sample_cal.get_power_scale_factor(sr, f, g)

        # Save the point so we don't duplicate
        self.pytest_points.append(
            {
                "sample_rate": int(sr),
                "frequency": f,
                "gain": g,
                "scale_factor": sf,
                "test": reason,
            }
        )

        # Check if the point was calculated correctly
        tolerance = 1e-5
        msg = "Scale factor not correctly calculated!\r\n"
        msg = "{}    Expected value:   {}\r\n".format(msg, sf)
        msg = "{}    Calculated value: {}\r\n".format(msg, csf)
        msg = "{}    Tolerance: {}\r\n".format(msg, tolerance)
        msg = "{}    Test: {}\r\n".format(msg, reason)
        msg = "{}    Sample Rate: {}({})\r\n".format(msg, sr / 1e6, sr_m / 1e6)
        msg = "{}    Frequency: {}({})\r\n".format(msg, f / 1e6, f_m / 1e6)
        msg = "{}    Gain: {}({})\r\n".format(msg, g, g_m)
        msg = "{}    Formula: -1 * (Gain - Frequency[GHz] - Sample Rate[MHz])\r\n".format(
            msg
        )
        assert self.is_close(sf, csf, tolerance), msg
        return True

    """ Create the dummy calibration file in the pytest temp directory """

    @pytest.fixture(autouse=True)
    def setup_calibration_file(self, tmpdir):
        # Only setup once
        if self.setup_complete:
            return

        # Create and save the temp directory and file
        self.tmpdir = tmpdir.strpath
        self.calibration_file = "{}".format(tmpdir.join("dummy_cal_file.json"))

        # Setup variables
        self.dummy_noise_figure = 10
        self.dummy_compression = -20
        self.test_repeat_times = 3

        # Sweep variables
        self.sample_rates = [10e6, 15.36e6, 40e6]
        self.gain_min = 40
        self.gain_max = 60
        self.gain_step = 10
        gains = list(range(self.gain_min, self.gain_max, self.gain_step)) + [
            self.gain_max
        ]
        self.frequency_min = 1000000000
        self.frequency_max = 3400000000
        self.frequency_step = 200000000
        frequencies = list(
            range(self.frequency_min, self.frequency_max, self.frequency_step)
        ) + [self.frequency_max]
        self.frequency_divisions = [[1299990000, 1300000000], [2199990000, 2200000000]]
        for div in self.frequency_divisions:
            if div[0] not in frequencies:
                frequencies.append(div[0])
            if div[1] not in frequencies:
                frequencies.append(div[1])
        frequencies = sorted(frequencies)

        # Start with blank cal data dicts
        cal_data = {}

        # Add the simple stuff to new cal format
        cal_data["calibration_datetime"] = "{}Z".format(
            datetime.datetime.utcnow().isoformat()
        )
        cal_data["sensor_uid"] = "SAMPLE_CALIBRATION"

        # Add the frequencie divisions to the calibration data
        cal_data["calibration_frequency_divisions"] = []
        for div in self.frequency_divisions:
            cal_data["calibration_frequency_divisions"].append(
                {"lower_bound": div[0], "upper_bound": div[1]}
            )

        # Add SR/CF lookup table
        cal_data["clock_rate_lookup_by_sample_rate"] = []
        for sr in self.sample_rates:
            cr = sr
            while cr <= 40e6:
                cr *= 2
            cr /= 2
            cal_data["clock_rate_lookup_by_sample_rate"].append(
                {"sample_rate": int(sr), "clock_frequency": int(cr)}
            )

        # Cycle through the sample rates, frequencies, and gains
        cal_data["calibration_points"] = []
        for k in range(len(self.sample_rates)):
            for i in range(len(frequencies)):
                for j in range(len(gains)):
                    # Create the scale factor that ensures easy interpolation
                    scale_factor = self.easy_sf(
                        self.sample_rates[k], frequencies[i], gains[j]
                    )

                    # Create the data point
                    cal_data["calibration_points"].append(
                        {
                            "sample_rate_sigan": int(self.sample_rates[k]),
                            "freq_sigan": frequencies[i],
                            "gain_sigan": gains[j],
                            "scale_factor": scale_factor,
                            "noise_figure": self.dummy_noise_figure,
                            "1dB_compression": self.dummy_compression,
                        }
                    )

        # Write the new json file
        with open(self.calibration_file, "w+") as file:
            json.dump(cal_data, file, indent=4)
            file.close()

        # Load the data back in
        self.sample_cal = calibration.load_from_json(self.calibration_file)

        # Create a list of previous points to ensure that we don't repeat
        self.pytest_points = []

        # Create sweep lists for test points
        self.srs = self.sample_rates
        self.gi_s = list(range(self.gain_min, self.gain_max, self.gain_step))
        self.fi_s = list(
            range(self.frequency_min, self.frequency_max, self.frequency_step)
        )
        self.g_s = self.gi_s + [self.gain_max]
        self.f_s = self.fi_s + [self.frequency_max]

        # Get a list of division frequencies
        self.div_fs = []
        for div in self.frequency_divisions:
            self.div_fs.append(div[0])
            self.div_fs.append(div[1])
        for f in self.div_fs:
            if f in self.f_s:
                self.f_s.remove(f)

        # Don't repeat test setup
        self.setup_complete = True

    """ Test SF determination at boundary points """

    def test_sf_bound_points(self):
        self.run_pytest_point(
            self.srs[0], self.frequency_min, self.gain_min, "Testing boundary points"
        )
        self.run_pytest_point(
            self.srs[0], self.frequency_max, self.gain_max, "Testing boundary points"
        )

    """ Test points without interpolation """

    def test_sf_no_interpolation_points(self):
        for i in range(4 * self.test_repeat_times):
            while True:
                g = self.g_s[self.rand_index(self.g_s)]
                f = self.f_s[self.rand_index(self.f_s)]
                if self.run_pytest_point(
                    self.srs[0], f, g, "Testing no interpolation points"
                ):
                    break

    """ Test points with frequency interpolation only """

    def test_sf_f_interpolation_points(self):
        for i in range(4 * self.test_repeat_times):
            while True:
                g = self.g_s[self.rand_index(self.g_s)]
                f = self.fi_s[self.rand_index(self.fi_s)]
                f_add = random.randint(1, int(self.frequency_step / 10e6) - 1) * 10e6
                if self.run_pytest_point(
                    self.srs[0], f + f_add, g, "Testing frequency interpolation points"
                ):
                    break

    """ Test points with gain interpolation only """

    def test_sf_g_interpolation_points(self):
        for i in range(4 * self.test_repeat_times):
            while True:
                g = self.gi_s[self.rand_index(self.gi_s)]
                f = self.f_s[self.rand_index(self.f_s)]
                g_add = random.randint(1, self.gain_step - 1)
                if self.run_pytest_point(
                    self.srs[0], f, g + g_add, "Testing gain interpolation points"
                ):
                    break

    """ Test points with frequency and gain interpolation only """

    def test_sf_g_f_interpolation_points(self):
        for i in range(4 * self.test_repeat_times):
            while True:
                g = self.gi_s[self.rand_index(self.gi_s)]
                f = self.fi_s[self.rand_index(self.fi_s)]
                f_add = random.randint(1, int(self.frequency_step / 10e6) - 1) * 10e6
                g_add = random.randint(1, self.gain_step - 1)
                if self.run_pytest_point(
                    self.srs[0],
                    f + f_add,
                    g + g_add,
                    "Testing frequency and gain interpolation points",
                ):
                    break

    """ Test points with a gain fudge factor """

    def test_g_fudge_points(self):
        for i in range(2 * self.test_repeat_times):
            while True:
                g = self.gain_min
                f = self.f_s[self.rand_index(self.f_s)]
                g_add = random.randint(1, self.gain_step - 1)
                if self.run_pytest_point(
                    self.srs[0], f, g - g_add, "Testing gain fudge points"
                ):
                    break
            while True:
                g = self.gain_max
                f = self.f_s[self.rand_index(self.f_s)]
                g_add = random.randint(1, self.gain_step - 1)
                if self.run_pytest_point(
                    self.srs[0], f, g + g_add, "Testing gain fudge points"
                ):
                    break

    """ Test points with a gain fudge factor and frequency interpolation """

    def test_g_fudge_f_interpolation_points(self):
        for i in range(2 * self.test_repeat_times):
            while True:
                g = self.gain_min
                f = self.fi_s[self.rand_index(self.fi_s)]
                f_add = random.randint(1, int(self.frequency_step / 10e6) - 1) * 10e6
                g_add = random.randint(1, self.gain_step - 1)
                if self.run_pytest_point(
                    self.srs[0],
                    f + f_add,
                    g - g_add,
                    "Testing gain fudge with frequency interpolation points",
                ):
                    break
            while True:
                g = self.gain_max
                f = self.fi_s[self.rand_index(self.fi_s)]
                f_add = random.randint(1, int(self.frequency_step / 10e6) - 1) * 10e6
                g_add = random.randint(1, self.gain_step - 1)
                if self.run_pytest_point(
                    self.srs[0],
                    f + f_add,
                    g + g_add,
                    "Testing gain fudge with frequency interpolation points",
                ):
                    break

    """ Test points with a gain fudge factor and out-of-bound frequencies """

    def test_g_fudge_f_oob_points(self):
        for i in range(self.test_repeat_times):
            while True:
                g = self.gain_min
                f = self.frequency_min
                f_add = random.randint(1, int(self.frequency_step / 10e6) - 1) * 10e6
                g_add = random.randint(1, self.gain_step - 1)
                if self.run_pytest_point(
                    self.srs[0],
                    f - f_add,
                    g - g_add,
                    "Testing gain fudge with out-of-bound frequency points",
                    f_m=f,
                ):
                    break
            while True:
                g = self.gain_max
                f = self.frequency_min
                f_add = random.randint(1, int(self.frequency_step / 10e6) - 1) * 10e6
                g_add = random.randint(1, self.gain_step - 1)
                if self.run_pytest_point(
                    self.srs[0],
                    f - f_add,
                    g + g_add,
                    "Testing gain fudge with out-of-bound frequency points",
                    f_m=f,
                ):
                    break
            while True:
                g = self.gain_max
                f = self.frequency_max
                f_add = random.randint(1, int(self.frequency_step / 10e6) - 1) * 10e6
                g_add = random.randint(1, self.gain_step - 1)
                if self.run_pytest_point(
                    self.srs[0],
                    f + f_add,
                    g + g_add,
                    "Testing gain fudge with out-of-bound frequency points",
                    f_m=f,
                ):
                    break
            while True:
                g = self.gain_min
                f = self.frequency_max
                f_add = random.randint(1, int(self.frequency_step / 10e6) - 1) * 10e6
                g_add = random.randint(1, self.gain_step - 1)
                if self.run_pytest_point(
                    self.srs[0],
                    f + f_add,
                    g - g_add,
                    "Testing gain fudge with out-of-bound frequency points",
                    f_m=f,
                ):
                    break

    """ Test points with gain interpolation and out-of-bound frequencies """

    def test_g_interpolation_f_oob_points(self):
        for i in range(2 * self.test_repeat_times):
            while True:
                g = self.gi_s[self.rand_index(self.gi_s)]
                f = self.frequency_min
                f_add = random.randint(1, int(self.frequency_step / 10e6) - 1) * 10e6
                g_add = random.randint(1, self.gain_step - 1)
                if self.run_pytest_point(
                    self.srs[0],
                    f - f_add,
                    g + g_add,
                    "Testing out-of-bound frequency with gain interpolation points",
                    f_m=f,
                ):
                    break
            while True:
                g = self.gi_s[self.rand_index(self.gi_s)]
                f = self.frequency_max
                f_add = random.randint(1, int(self.frequency_step / 10e6) - 1) * 10e6
                g_add = random.randint(1, self.gain_step - 1)
                if self.run_pytest_point(
                    self.srs[0],
                    f + f_add,
                    g + g_add,
                    "Testing out-of-bound frequency with gain interpolation points",
                    f_m=f,
                ):
                    break

    """ Test points with out-of-bound frequencies """

    def test_f_oob_points(self):
        for i in range(2 * self.test_repeat_times):
            while True:
                g = self.g_s[self.rand_index(self.g_s)]
                f = self.frequency_min
                f_add = random.randint(1, int(self.frequency_step / 10e6) - 1) * 10e6
                if self.run_pytest_point(
                    self.srs[0],
                    f - f_add,
                    g,
                    "Testing out-of-bound frequency points",
                    f_m=f,
                ):
                    break
            while True:
                g = self.g_s[self.rand_index(self.g_s)]
                f = self.frequency_max
                f_add = random.randint(1, int(self.frequency_step / 10e6) - 1) * 10e6
                if self.run_pytest_point(
                    self.srs[0],
                    f + f_add,
                    g,
                    "Testing out-of-bound frequency points",
                    f_m=f,
                ):
                    break

    """ Test points with division frequencies """

    def test_division_f_points(self):
        for i in range(self.test_repeat_times):
            for f in self.div_fs:
                while True:
                    g = self.g_s[self.rand_index(self.g_s)]
                    if self.run_pytest_point(
                        self.srs[0], f, g, "Testing division frequency points"
                    ):
                        break

    """ Test points with gain interpolation and division frequencies """

    def test_g_interpolation_division_f_points(self):
        for i in range(self.test_repeat_times):
            for f in self.div_fs:
                while True:
                    g = self.gi_s[self.rand_index(self.gi_s)]
                    g_add = random.randint(1, self.gain_step - 1)
                    if self.run_pytest_point(
                        self.srs[0],
                        f,
                        g + g_add,
                        "Testing division frequency with gain interpolation points",
                    ):
                        break

    """ Test points with gain fudge and division frequencies """

    def test_g_fudge_division_f_points(self):
        for i in range(self.test_repeat_times):
            for f in self.div_fs:
                while True:
                    g = self.gain_max
                    g_add = random.randint(1, self.gain_step - 1)
                    if self.run_pytest_point(
                        self.srs[0],
                        f,
                        g + g_add,
                        "Testing division frequency with gain fudge points",
                    ):
                        break

    """ Test points with in-division frequencies """

    def test_in_division_f_points(self):
        for j in range(self.test_repeat_times):
            for i in range(0, len(self.div_fs), 2):
                while True:
                    f = random.randint(self.div_fs[i] + 1, self.div_fs[i + 1] - 1)
                    g = self.g_s[self.rand_index(self.g_s)]
                    if self.run_pytest_point(
                        self.srs[0],
                        f,
                        g,
                        "Testing within division frequency points",
                        f_m=self.div_fs[i],
                    ):
                        break

    """ Test points with gain interpolation and in-division frequencies """

    def test_g_interpolation_in_division_f_points(self):
        for j in range(self.test_repeat_times):
            for i in range(0, len(self.div_fs), 2):
                while True:
                    f = random.randint(self.div_fs[i] + 1, self.div_fs[i + 1] - 1)
                    g = self.gi_s[self.rand_index(self.gi_s)]
                    g_add = random.randint(1, self.gain_step - 1)
                    if self.run_pytest_point(
                        self.srs[0],
                        f,
                        g + g_add,
                        "Testing within division frequency with gain interpolation points",
                        f_m=self.div_fs[i],
                    ):
                        break

    """ Test points with gain fudge and in-division frequencies """

    def test_g_fudge_in_division_f_points(self):
        for j in range(self.test_repeat_times):
            for i in range(0, len(self.div_fs), 2):
                while True:
                    f = random.randint(self.div_fs[i] + 1, self.div_fs[i + 1] - 1)
                    g = self.gain_max
                    g_add = random.randint(1, self.gain_step - 1)
                    if self.run_pytest_point(
                        self.srs[0],
                        f,
                        g + g_add,
                        "Testing within division frequency with gain fudge points",
                        f_m=self.div_fs[i],
                    ):
                        break

    """ Test points with gain and frequency interpolation at different sample rates """

    def test_sample_rate_points(self):
        for j in range(self.test_repeat_times):
            for i in range(len(self.srs)):
                while True:
                    g = self.gi_s[self.rand_index(self.gi_s)]
                    f = self.fi_s[self.rand_index(self.fi_s)]
                    f_add = (
                        random.randint(1, int(self.frequency_step / 10e6) - 1) * 10e6
                    )
                    g_add = random.randint(1, self.gain_step - 1)
                    if self.run_pytest_point(
                        self.srs[i],
                        f + f_add,
                        g + g_add,
                        "Testing different sample rate points",
                    ):
                        break

    """ Test points with gain and frequency interpolation at uncalibrated sample rates """

    def test_uncalibrated_sample_rate_points(self):
        for i in range(4 * self.test_repeat_times):
            while True:
                g = self.gi_s[self.rand_index(self.gi_s)]
                f = self.fi_s[self.rand_index(self.fi_s)]
                f_add = random.randint(1, int(self.frequency_step / 10e6) - 1) * 10e6
                g_add = random.randint(1, self.gain_step - 1)
                sr = 1e6 * random.randint(1, 40)
                if int(sr) in self.srs:
                    continue
                if self.run_pytest_point(
                    sr,
                    f + f_add,
                    g + g_add,
                    "Testing uncalibrated sample rate points",
                    sr_m=self.srs[0],
                ):
                    break
