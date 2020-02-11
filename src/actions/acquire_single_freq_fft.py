# What follows is a parameterizable description of the algorithm used by this
# action. The first line is the summary and should be written in plain text.
# Everything following that is the extended description, which can be written
# in Markdown and MathJax. Each name in curly brackets '{}' will be replaced
# with the value specified in the `description` method which can be found at
# the very bottom of this file. Since this parameterization step affects
# everything in curly brackets, math notation such as {m \over n} must be
# escaped to {{m \over n}}.
#
# To print out this docstring after parameterization, see
# REPO_ROOT/scripts/print_action_docstring.py. You can then paste that into the
# SCOS Markdown Editor (link below) to see the final rendering.
#
# Resources:
# - MathJax reference: https://math.meta.stackexchange.com/q/5020
# - Markdown reference: https://commonmark.org/help/
# - SCOS Markdown Editor: https://ntia.github.io/scos-md-editor/
#
r"""Apply m4s detector over {nffts} {fft_size}-pt FFTs at {frequency:.2f} MHz.

# {name}

## Radio setup and sample acquisition

This action first tunes the radio to {frequency:.2f} MHz and requests a sample
rate of {sample_rate:.2f} Msps and {gain} dB of gain.

It then begins acquiring, and discards an appropriate number of samples while
the radio's IQ balance algorithm runs. Then, ${nffts} \times {fft_size}$
samples are acquired gap-free.

## Time-domain processing

First, the ${nffts} \times {fft_size}$ continuous samples are acquired from
the radio. If specified, a voltage scaling factor is applied to the complex
time-domain signals. Then, the data is reshaped into a ${nffts} \times
{fft_size}$ matrix:

$$
\begin{{pmatrix}}
a_{{1,1}}      & a_{{1,2}}     & \cdots  & a_{{1,fft\_size}}     \\\\
a_{{2,1}}      & a_{{2,2}}     & \cdots  & a_{{2,fft\_size}}     \\\\
\vdots         & \vdots        & \ddots  & \vdots                \\\\
a_{{nffts,1}}  & a_{{nfts,2}}  & \cdots  & a_{{nfts,fft\_size}}  \\\\
\end{{pmatrix}}
$$

where $a_{{i,j}}$ is a complex time-domain sample.

At that point, a Flat Top window, defined as

$$w(n) = &0.2156 - 0.4160 \cos{{(2 \pi n / M)}} + 0.2781 \cos{{(4 \pi n / M)}} -
         &0.0836 \cos{{(6 \pi n / M)}} + 0.0069 \cos{{(8 \pi n / M)}}$$

where $M = {fft_size}$ is the number of points in the window, is applied to
each row of the matrix.

## Frequency-domain processing

After windowing, the data matrix is converted into the frequency domain using
an FFT, doing the equivalent of the DFT defined as

$$A_k = \sum_{{m=0}}^{{n-1}}
a_m \exp\left\\{{-2\pi i{{mk \over n}}\right\\}} \qquad k = 0,\ldots,n-1$$

The data matrix is then converted to pseudo-power by taking the square of the
magnitude of each complex sample individually, allowing power statistics to be
taken.

## Applying detector

Next, the M4S (min, max, mean, median, and sample) detector is applied to the
data matrix. The input to the detector is a matrix of size ${nffts} \times
{fft_size}$, and the output matrix is size $5 \times {fft_size}$, with the
first row representing the min of each _column_, the second row representing
the _max_ of each column, and so "sample" detector simple chooses one of the
{nffts} FFTs at random.

## Power conversion

To finish the power conversion, the samples are divided by the characteristic
impedance (50 ohms). The power is then referenced back to the RF power by
dividing further by 2. The powers are normalized to the FFT bin width by
dividing by the length of the FFT and converted to dBm. Finally, an FFT window
correction factor is added to the powers given by

$$ C_{{win}} = 20log \left( \frac{{1}}{{ mean \left( w(n) \right) }} \right)

The resulting matrix is real-valued, 32-bit floats representing dBm.

"""

import logging

import numpy as np
from django.core.files.base import ContentFile
from sigmf.sigmffile import SigMFFile

from capabilities import capabilities
from hardware import radio
from sensor import settings, utils
from status.utils import get_location

from .base import Action
from .utils import *

logger = logging.getLogger(__name__)

GLOBAL_INFO = {
    "core:datatype": "rf32_le",  # 32-bit float, Little Endian
    "core:version": "0.0.2",
}


class SingleFrequencyFftAcquisition(Action):
    """Perform m4s detection over requested number of single-frequency FFTs.

    :param name: the name of the action
    :param frequency: center frequency in Hz
    :param gain: requested gain in dB
    :param sample_rate: requested sample_rate in Hz
    :param fft_size: number of points in FFT (some 2^n)
    :param nffts: number of consecutive FFTs to pass to detector

    """

    def __init__(self, name, frequency, gain, sample_rate, fft_size, nffts):
        super(SingleFrequencyFftAcquisition, self).__init__()

        self.name = name
        self.frequency = frequency
        self.gain = gain
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.nffts = nffts
        self.radio = radio  # make instance variable to allow mocking
        self.enbw = None

    def __call__(self, schedule_entry_name, task_id):
        """This is the entrypoint function called by the scheduler."""
        from tasks.models import TaskResult

        # Raises TaskResult.DoesNotExist if no matching task result
        task_result = TaskResult.objects.get(
            schedule_entry__name=schedule_entry_name, task_id=task_id
        )

        self.test_required_components()
        self.configure_sdr()
        data = self.acquire_data()
        m4s_data = self.apply_detector(data)
        sigmf_md = self.build_sigmf_md(task_id)
        self.archive(task_result, m4s_data, sigmf_md)

    def test_required_components(self):
        """Fail acquisition if a required component is not available."""
        # self.radio.connect()
        if not self.radio.is_available:
            msg = "acquisition failed: SDR required but not available"
            raise RuntimeError(msg)

    def configure_sdr(self):
        self.set_sdr_sample_rate()
        self.set_sdr_frequency()
        self.set_sdr_gain()

    def set_sdr_gain(self):
        self.radio.gain = self.gain

    def set_sdr_sample_rate(self):
        self.radio.sample_rate = self.sample_rate
        self.sample_rate = self.radio.sample_rate

    def set_sdr_frequency(self):
        requested_frequency = self.frequency
        self.radio.frequency = requested_frequency
        self.frequency = self.radio.frequency

    def acquire_data(self):
        msg = "Acquiring {} FFTs at {} MHz"
        logger.debug(msg.format(self.nffts, self.frequency / 1e6))

        # Drop ~10 ms of samples
        nskip = int(0.01 * self.sample_rate)

        data = self.radio.acquire_time_domain_samples(
            self.nffts * self.fft_size, num_samples_skip=nskip
        )
        return data

    def apply_detector(self, data):
        complex_fft, self.enbw = get_frequency_domain_data(
            data, self.radio.sample_rate, self.fft_size
        )
        power_fft = convert_volts_to_watts(complex_fft)
        power_fft_m4s = apply_detector(power_fft)
        power_fft_dbm = convert_watts_to_dbm(power_fft_m4s)
        return power_fft_dbm

    def build_sigmf_md(self, task_id):
        logger.debug("Building SigMF metadata file")

        # Use the radio's actual reported sample rate instead of requested rate
        sample_rate = self.radio.sample_rate

        sigmf_md = SigMFFile()
        sigmf_md.set_global_info(GLOBAL_INFO)
        sigmf_md.set_global_field("core:sample_rate", sample_rate)

        sensor_def = capabilities["sensor_definition"]
        sensor_def["id"] = settings.FQDN
        sigmf_md.set_global_field("ntia-sensor:sensor", sensor_def)

        action_def = {
            "name": self.name,
            "description": self.description,
            "type": ["FrequencyDomain"],
        }

        sigmf_md.set_global_field("ntia-scos:action", action_def)
        sigmf_md.set_global_field("ntia-scos:task_id", task_id)

        capture_md = {
            "core:frequency": self.frequency,
            "core:datetime": utils.get_datetime_str_now(),
        }

        sigmf_md.add_capture(start_index=0, metadata=capture_md)

        location = get_location()

        for i, detector in enumerate(M4sDetector):
            frequency_domain_detection_md = {
                "ntia-core:annotation_type": "FrequencyDomainDetection",
                "ntia-algorithm:number_of_samples_in_fft": self.fft_size,
                "ntia-algorithm:window": "flattop",
                "ntia-algorithm:equivalent_noise_bandwidth": self.enbw,
                "ntia-algorithm:detector": detector.name + "_power",
                "ntia-algorithm:number_of_ffts": self.nffts,
                "ntia-algorithm:units": "dBm",
                "ntia-algorithm:reference": "not referenced",
            }

            if location:
                frequency_domain_detection_md["core:latitude"] = str(location.latitude)
                frequency_domain_detection_md["core:longitude"] = str(
                    location.longitude
                )

            sigmf_md.add_annotation(
                start_index=(i * self.fft_size),
                length=self.fft_size,
                metadata=frequency_domain_detection_md,
            )
            logger.debug("sample_count = " + str(self.fft_size))

        calibration_annotation_md = self.radio.create_calibration_annotation()
        sigmf_md.add_annotation(
            start_index=0,
            length=self.fft_size * len(M4sDetector),
            metadata=calibration_annotation_md,
        )

        return sigmf_md

    def archive(self, task_result, m4s_data, sigmf_md):
        from tasks.models import Acquisition

        logger.debug("data type = " + str(type(m4s_data[0][0])))
        logger.debug("Storing acquisition in database")

        name = (
            task_result.schedule_entry.name
            + "_"
            + str(task_result.task_id)
            + ".sigmf-data"
        )

        acquisition = Acquisition(task_result=task_result, metadata=sigmf_md._metadata)
        acquisition.data.save(name, ContentFile(m4s_data))
        acquisition.save()
        logger.debug("Saved new file at {}".format(acquisition.data.path))

    @property
    def description(self):
        defs = {
            "name": self.name,
            "frequency": self.frequency / 1e6,
            "sample_rate": self.sample_rate / 1e6,
            "fft_size": self.fft_size,
            "nffts": self.nffts,
            "gain": self.gain,
        }

        # __doc__ refers to the module docstring at the top of the file
        return __doc__.format(**defs)
