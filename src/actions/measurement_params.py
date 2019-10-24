class MeasurementParams:
    """
    class for holding parameters needed for spectrum monitoring measurement
    """

    def __init__(self, center_frequency, gain, sample_rate, duration_ms=None, fft_size=None, num_ffts=None):
        self.center_frequency = center_frequency
        self.gain = gain
        self.sample_rate = sample_rate
        self.duration_ms = duration_ms
        self.fft_size = fft_size
        self.num_ffts = num_ffts

    def get_num_samples(self):
        return int(self.sample_rate * self.duration_ms * 1e-3)
