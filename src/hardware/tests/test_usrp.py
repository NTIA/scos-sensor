"""Test aspects of RadioInterface with mocked USRP."""

import pytest

from hardware import usrp_iface

# Create the RadioInterface with the mock usrp_block
usrp_iface.connect()
if not usrp_iface.is_available:
    raise RuntimeError("Receiver is not available.")

rx = usrp_iface.radio


# Ensure the usrp can recover from acquisition errors
def test_acquire_samples_with_retries():
    """Acquire samples should retry without error up to `max_retries`."""
    max_retries = 5
    times_to_fail = 3
    rx.usrp.set_times_to_fail_recv(times_to_fail)

    try:
        rx.acquire_samples(1000, retries=max_retries)
    except RuntimeError:
        msg = "Acquisition failing {} times sequentially with {}\n"
        msg += "retries requested should NOT have raised an error."
        msg = msg.format(times_to_fail, max_retries)
        pytest.fail(msg)

    rx.usrp.set_times_to_fail_recv(0)


def test_acquire_samples_fails_when_over_max_retries():
    """After `max_retries`, an error should be thrown."""
    max_retries = 5
    times_to_fail = 7
    rx.usrp.set_times_to_fail_recv(times_to_fail)

    msg = "Acquisition failing {} times sequentially with {}\n"
    msg += "retries requested SHOULD have raised an error."
    msg = msg.format(times_to_fail, max_retries)
    with pytest.raises(RuntimeError):
        rx.acquire_samples(1000, 1000, max_retries)
        pytest.fail(msg)

    rx.usrp.set_times_to_fail_recv(0)


def test_tune_result():
    # Use a positive DSP frequency
    f_lo = 1.0e9
    f_dsp = 1.0e6
    rx.tune_frequency(f_lo, f_dsp)
    assert f_lo == rx.lo_freq and f_dsp == rx.dsp_freq

    # Use a 0Hz for DSP frequency
    f_lo = 1.0e9
    f_dsp = 0.0
    rx.frequency = f_lo
    assert f_lo == rx.lo_freq and f_dsp == rx.dsp_freq

    # Use a negative DSP frequency
    f_lo = 1.0e9
    f_dsp = -1.0e6
    rx.tune_frequency(f_lo, f_dsp)
    assert f_lo == rx.lo_freq and f_dsp == rx.dsp_freq


def test_scaled_data_acquisition():
    # Do an arbitrary data collection
    rx.frequency = 1900e6
    rx.gain = 20
    data = rx.acquire_samples(1000)

    # Pick an arbitrary sample and round to 5 decimal places
    datum = int((data[236] * 1e6).real)
    true_val = 104190

    # Assert the value
    msg = "Scale factor not correctly applied to acquisition.\n"
    msg += "Algorithm: {}\n".format(datum / 1e6)
    msg += "Expected: {}\n".format(true_val / 1e6)
    assert datum == true_val, msg


def test_set_sample_rate_also_sets_clock_rate():
    """Setting sample_rate should adjust clock_rate"""
    expected_clock_rate = 30720000

    rx.sample_rate = 15360000

    observed_clock_rate = rx.clock_rate

    assert expected_clock_rate == observed_clock_rate
