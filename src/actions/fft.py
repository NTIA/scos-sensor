from enum import Enum

import numpy as np
from scipy.signal import windows

from sensor import settings


class M4sDetector(Enum):
    min = 1
    max = 2
    mean = 3
    median = 4
    sample = 5


def m4s_detector(array):
    """Take min, max, mean, median, and random sample of n-dimensional array.

    Detector is applied along each column.

    :param array: an (m x n) array of real frequency-domain linear power values
    :returns: a (5 x n) in the order min, max, mean, median, sample in the case
              that `detector` is `m4s`, otherwise a (1 x n) array

    """
    amin = np.min(array, axis=0)
    amax = np.max(array, axis=0)
    mean = np.mean(array, axis=0)
    median = np.median(array, axis=0)
    random_sample = array[np.random.randint(0, array.shape[0], 1)][0]
    m4s = np.array([amin, amax, mean, median, random_sample], dtype=np.float32)

    return m4s


def get_frequency_domain_data(time_data, sample_rate, fft_size):
    # Get the fft window and its amplitude/energy correction factors
    fft_window = get_fft_window("Flat Top", fft_size)
    fft_window_acf = get_fft_window_correction(fft_window, "amplitude")
    fft_window_ecf = get_fft_window_correction(fft_window, "energy")
    fft_window_enbw = (fft_window_acf / fft_window_ecf) ** 2
    # Calculate the equivalent noise bandwidth of the bins
    enbw = sample_rate
    enbw *= fft_window_enbw
    enbw /= fft_size
    # Resize time data for FFTs
    num_ffts = int(len(time_data) / fft_size)
    time_data.resize((num_ffts, fft_size))
    # Apply the FFT window
    data = time_data * fft_window
    # Take and shift the fft (center frequency)
    complex_fft = np.fft.fft(data)
    complex_fft = np.fft.fftshift(complex_fft)
    complex_fft /= 2
    # Convert from V/Hz to V
    complex_fft /= fft_size
    # Apply the window's amplitude correction factor
    complex_fft *= fft_window_acf
    return complex_fft, enbw


def convert_volts_to_watts(complex_fft):
    # Convert to power P=V^2/R
    power_fft = np.abs(complex_fft)
    power_fft = np.square(power_fft)
    power_fft /= 50
    return power_fft


def apply_detector(power_fft):
    # Run the M4S detector
    power_fft_m4s = m4s_detector(power_fft)
    return power_fft_m4s


def convert_watts_to_dbm(power_fft):
    # If testing, don't flood output with divide-by-zero warnings from np.log10
    if settings.RUNNING_TESTS:
        np_error_settings_savepoint = np.seterr(divide="ignore")
    # Convert to dBm dBm = dB +30; dB = 10log(W)
    power_fft_dbm = 10 * np.log10(power_fft) + 30
    return power_fft_dbm


def get_fft_window(window_type, window_length):
    # Generate the window with the right number of points
    window = None
    if window_type == "Bartlett":
        window = windows.bartlett(window_length)
    if window_type == "Blackman":
        window = windows.blackman(window_length)
    if window_type == "Blackman Harris":
        window = windows.blackmanharris(window_length)
    if window_type == "Flat Top":
        window = windows.flattop(window_length)
    if window_type == "Hamming":
        window = windows.hamming(window_length)
    if window_type == "Hanning":
        window = windows.hann(window_length)

    # If no window matched, use a rectangular window
    if window is None:
        window = np.ones(window_length)

    # Return the window
    return window


def get_fft_window_correction(window, correction_type="amplitude"):
    # Calculate the requested correction factor
    window_correction = 1  # Assume no correction
    if correction_type == "amplitude":
        window_correction = 1 / np.mean(window)
    if correction_type == "energy":
        window_correction = np.sqrt(1 / np.mean(window ** 2))

    # Return the window correction factor
    return window_correction


def get_fft_frequencies(fft_size, sample_rate, center_frequency):
    frequency_info = {}
    time_step = 1 / sample_rate
    frequencies = np.fft.fftfreq(fft_size, time_step)
    frequencies = np.fft.fftshift(frequencies) + center_frequency
    return frequencies
