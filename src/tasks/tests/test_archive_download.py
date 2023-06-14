import os
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
        claimed_sha512 = md["global"]["core:sha512"]
        actual_sha512 = sigmf.sigmf_hash.calculate_sha512(datafile)

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
        sigmf_archive_contents = sigmf.archive.extract(tf.name)
        assert len(sigmf_archive_contents) == 3
