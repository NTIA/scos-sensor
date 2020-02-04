import numpy as np
from scipy.signal import windows

from status.utils import get_location


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


def get_fft_frequencies(data, sample_rate, center_frequency):
    frequency_info = {}
    time_step = 1 / sample_rate
    frequencies = np.fft.fftfreq(data.size, time_step)
    frequencies = np.fft.fftshift(frequencies) + center_frequency
    return frequencies


def get_coordinate_system_sigmf():
    return {
        "id": "WGS 1984",
        "coordinate_system_type": "GeographicCoordinateSystem",
        "distance_unit": "decimal degrees",
        "time_unit": "seconds",
    }


def get_sensor_location_sigmf(sensor):
    database_location = get_location()
    if database_location:
        if "location" not in sensor:
            sensor["location"] = {}
        if "x" not in sensor["location"] or not sensor["location"]["x"]:
            sensor["location"]["x"] = database_location.longitude
        if "y" not in sensor["location"] or not sensor["location"]["y"]:
            sensor["location"]["y"] = database_location.latitude
