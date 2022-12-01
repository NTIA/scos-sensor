import os
import shutil
import tempfile

import numpy as np
import sigmf.sigmffile
from rest_framework import status

import sensor.settings
from test_utils.task_test_utils import (
    HTTPS_KWARG,
    reverse_archive,
    reverse_archive_all,
    simulate_frequency_fft_acquisitions,
    simulate_multirec_acquisition,
)


def test_single_acquisition_archive_download(admin_client, test_scheduler):
    entry_name = simulate_frequency_fft_acquisitions(admin_client, n=1)
    task_id = 1
    url = reverse_archive(entry_name, task_id)
    disposition = 'attachment; filename="{}_test_acq_1.sigmf"'
    disposition = disposition.format(sensor.settings.FQDN)
    response = admin_client.get(url, **HTTPS_KWARG)

    assert response.status_code == status.HTTP_200_OK
    assert response["content-disposition"] == disposition
    assert response["content-type"] == "application/x-tar"

    with tempfile.NamedTemporaryFile() as tf:
        for content in response.streaming_content:
            tf.write(content)
        tf.flush()

        sigmf_archive_contents = sigmf.sigmffile.fromarchive(tf.name)
        md = sigmf_archive_contents._metadata
        datafile = sigmf_archive_contents.data_file
        datafile_actual_size = os.stat(datafile).st_size
        claimed_sha512 = md["global"]["core:sha512"]
        # number_of_sample_arrays = len(md["annotations"])
        number_of_sample_arrays = 1
        cal_annotation = list(
            filter(
                lambda a: a["ntia-core:annotation_type"] == "CalibrationAnnotation",
                md["annotations"],
            )
        )[0]
        samples_per_array = cal_annotation["core:sample_count"]
        sample_array_size = samples_per_array * np.float32(0.0).nbytes
        datafile_expected_size = number_of_sample_arrays * sample_array_size
        actual_sha512 = sigmf.sigmf_hash.calculate_sha512(datafile)

        assert datafile_actual_size == datafile_expected_size
        assert claimed_sha512 == actual_sha512


def test_multirec_acquisition_archive_download(admin_client, test_scheduler):
    entry_name = simulate_multirec_acquisition(admin_client)
    task_id = 1
    url = reverse_archive(entry_name, task_id)
    disposition = 'attachment; filename="{}_test_multirec_acq_1.sigmf"'
    disposition = disposition.format(sensor.settings.FQDN)
    response = admin_client.get(url, **HTTPS_KWARG)

    assert response.status_code == status.HTTP_200_OK
    assert response["content-disposition"] == disposition
    assert response["content-type"] == "application/x-tar"

    with tempfile.NamedTemporaryFile() as tf:
        for content in response.streaming_content:
            tf.write(content)
        tf.flush()

        sigmf_archive_contents = sigmf.archive.extract(tf.name)
        assert len(sigmf_archive_contents) == 10


def test_all_acquisitions_archive_download(admin_client, test_scheduler, tmpdir):
    entry_name = simulate_frequency_fft_acquisitions(admin_client, n=3)
    url = reverse_archive_all(entry_name)
    disposition = 'attachment; filename="{}_test_multiple_acq.sigmf"'
    disposition = disposition.format(sensor.settings.FQDN)
    response = admin_client.get(url, **HTTPS_KWARG)

    assert response.status_code == status.HTTP_200_OK
    assert response["content-disposition"] == disposition
    assert response["content-type"] == "application/x-tar"

    with tempfile.NamedTemporaryFile() as tf:
        for content in response.streaming_content:
            tf.write(content)
        tf.flush()
        shutil.copy(tf.name, os.path.join("/home/jhaze/Desktop", "test_all_acquisitions_archive_download.tar"))
        sigmf_archive_contents = sigmf.archive.extract(tf.name)
        assert len(sigmf_archive_contents) == 3
