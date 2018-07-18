""" Test aspects of RadioInterface """

import pytest
from actions import usrp


# Create the RadioInterface with the mock usrp_block
usrp.connect(use_mock_usrp=True)
if not usrp.is_available:
    raise RuntimeError("Receiver is not available.")
rx = usrp.radio


# Ensure the usrp can recover from acquisition errors
def test_acquisition_errors():
    """
        The mock usrp_block will return "bad" data equal to
        the number of times aquire_samples() has been called
        until the reset_bad_acquisitions() has been called
    """
    rx.usrp.reset_bad_acquisitions()
    max_retries = 5
    for i in range(max_retries+2):
        if i <= max_retries:
            try:
                rx.acquire_samples(1000, 1000, max_retries)
            except RuntimeError:
                msg = "Acquisition failing {} sequentially with {}\r\n"
                msg += "retries requested should NOT have raised an error."
                msg = msg.format(i, max_retries)
                pytest.fail(msg)
        else:
            msg = "Acquisition failing {} sequentially with {}\r\n"
            msg += "retries requested SHOULD have raised an error."
            msg = msg.format(i, max_retries)
            with pytest.raises(RuntimeError, message=msg):
                rx.acquire_samples(1000, 1000, max_retries)
    rx.usrp.reset_bad_acquisitions()
    return


def test_tune_result_parsing():
    # Use a positive DSP frequency
    f_lo = 1.0e9
    f_dsp = 1.0e6
    rx.tune_frequency(f_lo, f_dsp)

    # Assert the parsing
    msg = "Tune result parsing failed.\r\n"
    msg += "Set LO:  {}, Parsed LO:  {}\r\n".format(f_lo, rx.lo_freq)
    msg += "Set DSP: {}, Parsed DSP: {}\r\n".format(f_dsp, rx.dsp_freq)
    assert (f_lo == rx.lo_freq and f_dsp == rx.dsp_freq), msg

    # Use a 0Hz for DSP frequency
    f_lo = 1.0e9
    f_dsp = 0.0
    rx.frequency = f_lo

    # Assert the parsing
    msg = "Tune result parsing failed.\r\n"
    msg += "Set LO:  {}, Parsed LO:  {}\r\n".format(f_lo, rx.lo_freq)
    msg += "Set DSP: {}, Parsed DSP: {}\r\n".format(f_dsp, rx.dsp_freq)
    assert (f_lo == rx.lo_freq and f_dsp == rx.dsp_freq), msg

    # Use a negative DSP frequency
    f_lo = 1.0e9
    f_dsp = -1.0e6
    rx.tune_frequency(f_lo, f_dsp)

    # Assert the parsing
    msg = "Tune result parsing failed.\r\n"
    msg += "Set LO:  {}, Parsed LO:  {}\r\n".format(f_lo, rx.lo_freq)
    msg += "Set DSP: {}, Parsed DSP: {}\r\n".format(f_dsp, rx.dsp_freq)
    assert (f_lo == rx.lo_freq and f_dsp == rx.dsp_freq), msg


def test_scaled_data_acquisition():
    # Do an arbitrary data collection
    rx.usrp.reset_bad_acquisitions()
    rx.frequency = 1900e6
    rx.gain = 23
    data = rx.acquire_samples(1000)

    # Pick an arbitrary sample and round to 5 decimal places
    datum = int(data[236]*1e6)
    true_val = 76415

    # Assert the value
    msg = "Scale factor not correctly applied to acquisition.\r\n"
    msg += "Algorithm: {}\r\n".format(datum/1e6)
    msg += "Expected: {}\r\n".format(true_val/1e6)
    assert (datum == true_val), msg
