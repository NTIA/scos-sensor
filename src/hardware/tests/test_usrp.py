"""Test aspects of RadioInterface with mocked USRP."""

import pytest
from hardware import usrp_iface

# Create the RadioInterface with the mock usrp_block
usrp_iface.connect()
if not usrp_iface.is_available:
    raise RuntimeError("Receiver is not available.")

rx = usrp_iface.radio


# Ensure the usrp can recover from acquisition errors
def test_acquisition_errors():
    """Test USRP bad acquisitions handled gracefully up to max_retries.

    The mock usrp_block will return "bad" data equal to the number of times
    aquire_samples() has been called until the reset_bad_acquisitions() has
    been called.

    """
    rx.usrp.reset_bad_acquisitions()
    max_retries = 5
    for i in range(max_retries + 2):
        if i <= max_retries:
            try:
                rx.acquire_samples(1000, 1000, max_retries)
            except RuntimeError:
                msg = "Acquisition failing {} sequentially with {}\n"
                msg += "retries requested should NOT have raised an error."
                msg = msg.format(i, max_retries)
                pytest.fail(msg)
        else:
            msg = "Acquisition failing {} sequentially with {}\n"
            msg += "retries requested SHOULD have raised an error."
            msg = msg.format(i, max_retries)
            with pytest.raises(RuntimeError, message=msg):
                rx.acquire_samples(1000, 1000, max_retries)

    rx.usrp.reset_bad_acquisitions()


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
    rx.usrp.reset_bad_acquisitions()
    rx.frequency = 1900e6
    rx.gain = 20
    data = rx.acquire_samples(1000)

    # Pick an arbitrary sample and round to 5 decimal places
    datum = int(data[236] * 1e6)
    true_val = 104190

    # Assert the value
    msg = "Scale factor not correctly applied to acquisition.\n"
    msg += "Algorithm: {}\n".format(datum / 1e6)
    msg += "Expected: {}\n".format(true_val / 1e6)
    assert (datum == true_val), msg
