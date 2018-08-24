"""Mock usrp_block."""

import numpy as np


class MockUsrpBlock(object):
    def __init__(self):
        self.auto_dc_offset = False
        self.gain = 0

        self.total_fail_results = 0
        self.current_fail_results = 0

    def set_auto_dc_offset(self, val):
        self.auto_dc_offset = val

    def finite_acquisition(self, n):
        if self.current_fail_results < self.total_fail_results:
            self.current_fail_results += 1
            return []

        self.current_fail_results = 0
        self.total_fail_results += 1
        return np.ones(n).tolist()

    def reset_bad_acquisitions(self):
        self.total_fail_results = 0
        self.current_fail_results = 0

    def set_center_freq(self, f_lo, f_dsp):
        f_lo /= 1e6
        f_dsp /= 1e6
        mock_response = "    Target RF  Freq: {} (MHz)\r\n"
        mock_response += "    Actual RF  Freq: {} (MHz)\r\n"
        mock_response += "    Target DSP Freq: {} (MHz)\r\n"
        mock_response += "    Actual DSP Freq: {} (MHz)\r\n"
        mock_response = mock_response.format(f_lo, f_lo, f_dsp, f_dsp)
        return mock_response

    def set_gain(self, g):
        self.gain = g

    def get_gain(self):
        return self.gain
