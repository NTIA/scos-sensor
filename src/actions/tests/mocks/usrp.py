"""Mock the usrp module."""

import numpy as np


driver_is_available = True
is_available = False
radio = None


def connect():
    global is_available
    global radio
    is_available = True
    radio = RadioInterfaceMock()
    return True


class RadioInterfaceMock(object):
    def __init__(self):
        self.sample_rate = 10e6
        self.clock_rate = 10e6
        self.frequency = 400e6
        self.gain = 30

    def acquire_samples(self, n):
        """Create the array [0.1] * 16 + [0.2] * 16 + ... until n runs out."""
        fft_size = 16
        r = np.zeros(n)
        final = n // fft_size
        for i in range(n // fft_size):
            r[i*fft_size:(i + 1)*fft_size] = [0.1 * (i + 1)] * fft_size

        remainder = n % fft_size
        if remainder:
            r[final*fft_size:n] = [0.1 * (final + 1)] * remainder

        return r
