import os
import tempfile

import numpy as np
from rest_framework import status

import sigmf.sigmffile

#from actions.mock_acquire import TEST_DATA_SHA512
from acquisitions.tests.utils import (
    reverse_acquisition_archive,
    simulate_acquisitions,
    HTTPS_KWARG
)


def test_archive_download(user_client, testclock):
    entry_name = simulate_acquisitions(user_client, n=1)
    task_id = 1
    url = reverse_acquisition_archive(entry_name, task_id)
    disposition = 'attachment; filename="test_acq_1.sigmf"'
    response = user_client.get(url, **HTTPS_KWARG)

    assert response.status_code == status.HTTP_200_OK
    assert response['content-disposition'] == disposition
    assert response['content-type'] == 'application/x-tar'
    assert response['content-length'] == '10240'

    with tempfile.NamedTemporaryFile() as tf:
        tf.write(response.content)
        sigmf_archive_contents = sigmf.sigmffile.fromarchive(tf.name)
        md = sigmf_archive_contents._metadata
        datafile = sigmf_archive_contents.data_file
        datafile_actual_size = os.stat(datafile).st_size
        claimed_sha512 = md['global']['core:sha512']
        number_of_samples = len(md['annotations'])
        sample_count = md['annotations'][0]['core:sample_count']
        sample_size = sample_count * np.float64(0.0).nbytes
        datafile_expected_size = number_of_samples * sample_size
        actual_sha512 = sigmf.sigmf_hash.calculate_sha512(datafile)

        assert datafile_actual_size == datafile_expected_size
        assert claimed_sha512 == actual_sha512
