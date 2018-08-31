"""Mock the gnuradio gr-uhd usrp module."""

from collections import namedtuple

import numpy as np


tune_result_params = ['actual_dsp_freq', 'actual_rf_freq']
MockTuneResult = namedtuple('MockTuneResult', tune_result_params)


class MockUsrpBlock(object):
    def __init__(self):
        self.auto_dc_offset = False
        self.f_lo = 700e6
        self.f_dsp = 0
        self.samp_rate = 10e6
        self.clock_rate = 40e6
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

    def get_center_freq(self):
        return self.f_lo + self.f_dsp

    def set_center_freq(self, f_lo, f_dsp):
        self.f_lo = f_lo
        self.f_dsp = f_dsp
        return MockTuneResult(actual_dsp_freq=f_dsp, actual_rf_freq=f_lo)

    def set_samp_rate(self, rate):
        self.samp_rate = rate

    def get_samp_rate(self):
        return self.samp_rate

    def get_clock_rate(self):
        return self.clock_rate

    def set_clock_rate(self, rate):
        self.clock_rate = rate

    def set_gain(self, g):
        self.gain = g

    def get_gain(self):
        return self.gain
