"""Take an acquisition."""

from datetime import datetime
from itertools import compress

from marshmallow import Schema, fields
from marshmallow.validate import Range, OneOf
import numpy as np

from commsensor import radio
from commsensor.acquisition import Acquisition
from commsensor.database import db
from commsensor.events import EventDescriptor
from commsensor.logging import log
from commsensor.sigmf.sigmffile import SigMFFile

from .base import Action


GLOBAL_INFO = {
    "core:datatype": "f32_le",  # 32-bit float, Little Endian
    "core:version": "0.0.1"
}


SIGMF_DATETIME_ISO8601_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def get_sigmf_iso8601_datetime_now():
    return datetime.isoformat(datetime.utcnow()) + 'Z'


def parse_iso8601_datetime(d):
    return datetime.strptime(d, SIGMF_DATETIME_ISO8601_FMT)


def acquire(edid, *, frequency, sample_rate, fft_size, nffts, detector):
    """Take an acquisition.

    :param frequency: target center frequency
    :param sample_rate: target sample rate
    :param fft_size: number of FFT bins
    :param nffts: number of FFTs to pass to detector
    :param detector: one of: 'peak', 'mean', 'm4' (only 'mean' implemented)

    """
    required_components = (radio.is_available,)
    component_names = ("radio",)
    missing_components = (not rc for rc in required_components)
    if any(missing_components):
        missing = tuple(compress(component_names, missing_components))
        msg = "acquisition failed: {} required but not available"
        raise RuntimeError(msg.format(missing))

    log.info("acquiring {} FFTs at {} MHz".format(nffts, frequency / 1e6))

    # FIXME
    gain = 30
    scale_factor = 0.01

    radio.usrp.sample_rate = sample_rate
    radio.usrp.frequency = frequency
    radio.usrp.gain = gain
    tdata = radio.usrp.acquire_samples(fft_size * nffts)

    window = np.blackman(fft_size)
    window_power = sum(tap*tap for tap in window)
    impedance = 50.0  # ohms
    Vsq2W_dB = -10.0 * np.log10(fft_size * window_power * impedance)

    tdata_scaled = tdata * scale_factor
    tdata_vectorized = tdata_scaled.reshape((nffts, fft_size))
    tdata_windowed = tdata_vectorized * window
    fdata = np.fft.fft(tdata_windowed)
    fdata_watts = np.square(np.abs(fdata))
    # TODO: implement peak detector
    # sum, NOT np.sum: sum adds element-wise but keeps final array of fftLen,
    # np.sum sums final list elements as well
    fdata_watts_mean = sum(fdata_watts) / nffts
    fdata_dbm = 10 * np.log10(fdata_watts_mean) + 30 + Vsq2W_dB
    fdata_dbm_shifted = np.fft.fftshift(fdata_dbm)  # shift fc to center

    # data_msg['data'] = list(fdata_dbm_shifted)  # json cannot encode np array
    # data_msg['sampleRate'] = radio.usrp.sample_rate


TEST_DATA_SHA512 = ("62171ba5e622232987f367c6f3cea85d"
                    "116a88a2e385dd07b54dc0dcd04c74da"
                    "f8027f7993af8356ea29ad6c64818bda"
                    "f2c5beb89efc0f8bc2c7838268535cda")


class TestAcquisition(Action):
    """Test an acquisition without using the radio."""
    def __call__(self, event_descriptor_id, event_id):
        frequency = self.frequency
        sample_rate = self.sample_rate
        fft_size = self.fft_size
        nffts = self.nffts
        detector = self.detector

        parent_evtdesc = EventDescriptor.query.get(event_descriptor_id)

        warning = "parent event descriptor {} doesn't exist - canceling action"
        assert parent_evtdesc, warning.format(event_descriptor_id)

        sigmf_md = SigMFFile()
        sigmf_md.set_global_field("core:datatype", "rf32_le")
        sigmf_md.set_global_field("core:sample_rate", sample_rate)
        sigmf_md.set_global_field("core:description",
                                  "test acquisition {}".format(event_id))

        data = np.arange(fft_size, dtype=np.float32).tobytes()

        capture_md = {
            "core:frequency": frequency,
            "core:time": get_sigmf_iso8601_datetime_now()
        }

        sigmf_md.add_capture(start_index=0, metadata=capture_md)

        annotation_md = {
            "core:latitude": 40.0,
            "core:longitude": -105.0,
            "scos:detector": detector
        }

        sigmf_md.add_annotation(start_index=0,
                                length=fft_size,
                                metadata=annotation_md)

        log.info("running test acquisition")

        acq = Acquisition(id=event_id, metadata_=sigmf_md, data=data)
        parent_evtdesc.acquisitions.append(acq)
        db.session.commit()


# TODO: determine this elsewhere and import
CAPABILITIES_MIN_FREQ = 400e6
CAPABILITIES_MAX_FREQ = 6000e6
CAPABILITIES_MIN_SRATE = 1000
CAPABILITIES_MAX_SRATE = 40e6
CAPABILITIES_DETECTORS = ["mean", "peak", "m4"]

# error strings
detector_err = "Invalid choice. {input!r} not in {choices!r}"


frequency_md = {
    "description": "target center frequency"
}
sample_rate_md = {
    "description": "target sample rate"
}
fft_size_md = {
    "description": "number of FFT bins",
    "multipleOf": 128
}
nffts_md = {
    "description": "number of consecutive FFTs to pass to detector"
}
detector_md = {
    "description": "type of detector to run over acquisition"
}


class TestAcquisitionSchema(Schema):
    """
    This is not a registered callback by default, but is automatically
    registered by the testing framework when tests are being run, so it can be
    referred to without any extra setup within a test case that requests the
    `client` fixture.
    """

    frequency = fields.Number(required=True,
                              validate=Range(min=CAPABILITIES_MIN_FREQ,
                                             max=CAPABILITIES_MAX_FREQ),
                              **frequency_md)
    sample_rate = fields.Number(required=True,
                                validate=Range(min=CAPABILITIES_MIN_SRATE,
                                               max=CAPABILITIES_MAX_SRATE),
                                **sample_rate_md)
    fft_size = fields.Integer(required=True,
                              validate=Range(min=128, max=8192), **fft_size_md)
    nffts = fields.Integer(required=True,
                           validate=Range(min=1), **nffts_md)
    detector = fields.String(required=True,
                             validate=OneOf(choices=CAPABILITIES_DETECTORS,
                                            error=detector_err),
                             **detector_md)

    class Meta:
        ordered = True


test_acquisition_schema = TestAcquisitionSchema(strict=True)
test_acquire = TestAcquisition(test_acquisition_schema)
