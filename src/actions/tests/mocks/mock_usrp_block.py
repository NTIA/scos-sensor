"""Mock the usrp_block module."""

import numpy as np


class mock_usrp_block(object):

    auto_dc_offset = False
    gain = 0

    # Hold variables for acquisition test
    total_fail_results = 0
    current_fail_results = 0

    def __init__(self):
        return

    def set_auto_dc_offset(self, val):
        self.auto_dc_offset = val

    def finite_acquisition(self, n):
        if self.current_fail_results < self.total_fail_results:
            self.current_fail_results = self.current_fail_results + 1
            return []
        else:
            self.current_fail_results = 0
            self.total_fail_results = self.total_fail_results + 1
            return np.ones(n).tolist()

    def reset_bad_acquisitions(self):
        self.total_fail_results = 0
        self.current_fail_results = 0
        return

    def set_center_freq(self, f_lo, f_dsp):
        f_lo = f_lo/1e6
        f_dsp = f_dsp/1e6
        return (
            "    Target RF  Freq: {} (MHz)\r\n" +
            "    Actual RF  Freq: {} (MHz)\r\n" +
            "    Target DSP Freq: {} (MHz)\r\n" +
            "    Actual DSP Freq: {} (MHz)\r\n"
        ).format(
            f_lo, f_lo, f_dsp, f_dsp
        )

    def set_gain(self, g):
        self.gain = g

    def get_gain(self):
        return self.gain
