"""Mock the UHD USRP module."""

from collections import namedtuple

import numpy as np

tune_result_params = ["actual_dsp_freq", "actual_rf_freq"]
MockTuneResult = namedtuple("MockTuneResult", tune_result_params)


class MockUsrp(object):
    def __init__(self, randomize_values=False):
        self.auto_dc_offset = False
        self.f_lo = 700e6
        self.f_dsp = 0
        self.samp_rate = 10e6
        self.clock_rate = 40e6
        self.gain = 0

        # Simulate returning less than the requested number of samples from
        # self.recv_num_samps
        self.times_to_fail_recv = 0
        self.times_failed_recv = 0

        self.randomize_values = randomize_values

    def set_auto_dc_offset(self, val):
        self.auto_dc_offset = val

    def recv_num_samps(self, n, fc, fs, channels, gain):
        if self.times_failed_recv < self.times_to_fail_recv:
            self.times_failed_recv += 1
            return np.ones((1, 0), dtype=np.complex64)

        if self.randomize_values:
            i = np.random.normal(0.5, 0.5, n)
            q = np.random.normal(0.5, 0.5, n)
            rand_iq = np.empty((1, n), dtype=np.complex64)
            rand_iq[0].real = i
            rand_iq[0].imag = q
            return rand_iq
        else:
            return np.ones((1, n), dtype=np.complex64)

    def set_times_to_fail_recv(self, n):
        self.times_to_fail_recv = n
        self.times_failed_recv = 0

    def get_rx_freq(self):
        return self.f_lo + self.f_dsp

    def set_rx_freq(self, f_lo, f_dsp):
        self.f_lo = f_lo
        self.f_dsp = f_dsp
        return MockTuneResult(actual_dsp_freq=f_dsp, actual_rf_freq=f_lo)

    def set_rx_rate(self, rate):
        self.samp_rate = rate

    def get_rx_rate(self):
        return self.samp_rate

    def get_master_clock_rate(self):
        return self.clock_rate

    def set_master_clock_rate(self, rate):
        self.clock_rate = rate

    def set_rx_gain(self, g):
        self.gain = g

    def get_rx_gain(self):
        return self.gain
