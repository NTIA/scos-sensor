import os
import tempfile

import numpy as np
import sigmf.sigmffile
from rest_framework import status

import sensor.settings
from tasks.tests.utils import (
    HTTPS_KWARG,
    reverse_archive,
    reverse_archive_all,
    simulate_acquisitions,
    simulate_multirec_acquisition,
)


def test_single_acquisition_archive_download(user_client, test_scheduler):
    entry_name = simulate_acquisitions(user_client, n=1)
    task_id = 1
    url = reverse_archive(entry_name, task_id)
    disposition = 'attachment; filename="{}_test_acq_1.sigmf"'
    disposition = disposition.format(sensor.settings.FQDN)
    response = user_client.get(url, **HTTPS_KWARG)

    assert response.status_code == status.HTTP_200_OK
    assert response["content-disposition"] == disposition
    assert response["content-type"] == "application/x-tar"

    with tempfile.NamedTemporaryFile() as tf:
        for content in response.streaming_content:
            tf.write(content)

        sigmf_archive_contents = sigmf.sigmffile.fromarchive(tf.name)
        md = sigmf_archive_contents._metadata
        datafile = sigmf_archive_contents.data_file
        datafile_actual_size = os.stat(datafile).st_size
        claimed_sha512 = md["global"]["core:sha512"]
        total_samples = 0
        for annotation in md["annotations"]:
            if annotation["ntia-core:annotation_type"] == "FrequencyDomainDetection":
                total_samples += annotation["core:sample_count"]
        datafile_expected_size = total_samples * np.float32(0.0).nbytes
        actual_sha512 = sigmf.sigmf_hash.calculate_sha512(datafile)
        assert datafile_actual_size == datafile_expected_size
        assert claimed_sha512 == actual_sha512


def test_multirec_acquisition_archive_download(user_client, test_scheduler):
    entry_name = simulate_multirec_acquisition(user_client)
    task_id = 1
    url = reverse_archive(entry_name, task_id)
    disposition = 'attachment; filename="{}_test_multirec_acq_1.sigmf"'
    disposition = disposition.format(sensor.settings.FQDN)
    response = user_client.get(url, **HTTPS_KWARG)

    assert response.status_code == status.HTTP_200_OK
    assert response["content-disposition"] == disposition
    assert response["content-type"] == "application/x-tar"

    with tempfile.NamedTemporaryFile() as tf:
        for content in response.streaming_content:
            tf.write(content)
        tf.flush()

        sigmf_archive_contents = sigmf.archive.extract(tf.name)
        assert len(sigmf_archive_contents) == 3


def test_all_acquisitions_archive_download(user_client, test_scheduler, tmpdir):
    entry_name = simulate_acquisitions(user_client, n=3)
    url = reverse_archive_all(entry_name)
    disposition = 'attachment; filename="{}_test_multiple_acq.sigmf"'
    disposition = disposition.format(sensor.settings.FQDN)
    response = user_client.get(url, **HTTPS_KWARG)

    assert response.status_code == status.HTTP_200_OK
    assert response["content-disposition"] == disposition
    assert response["content-type"] == "application/x-tar"

    import os.path

    perm_temp_fname = os.path.join(tmpdir, "test_sigmf.tar")
    with open(perm_temp_fname, "wb+") as tf:
        for content in response.streaming_content:
            tf.write(content)

    sigmf_archive_contents = sigmf.archive.extract(perm_temp_fname)
    assert len(sigmf_archive_contents) == 3
