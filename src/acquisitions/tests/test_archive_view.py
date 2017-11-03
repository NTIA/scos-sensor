import os
import tempfile

import numpy as np
import pytest
from rest_framework import status

import sigmf.sigmffile

from acquisitions.tests.utils import (
    reverse_acquisition_archive, simulate_acquisitions, HTTPS_KWARG)


@pytest.mark.django_db
def test_archive_download(client, testclock, test_user):
    client.login(username=test_user.username, password=test_user.password)

    entry_name = simulate_acquisitions(client, n=1)
    task_id = 1
    url = reverse_acquisition_archive(entry_name, task_id)
    r = client.get(url, **HTTPS_KWARG)

    assert r.status_code == status.HTTP_200_OK
    assert r['content-disposition'] == (
        'attachment; filename="test_acq_1.sigmf"')
    assert r['content-type'] == 'application/x-tar'
    assert r['content-length'] == '10240'

    with tempfile.NamedTemporaryFile() as tf:
        tf.write(r.content)
        sigmf_archive_contents = sigmf.sigmffile.fromarchive(tf.name)
        md = sigmf_archive_contents._metadata
        datafile = sigmf_archive_contents.data_file
        datafile_actual_size = os.stat(datafile).st_size
        nsamples = md['annotations'][0]['core:sample_count']
        datafile_expected_size = nsamples * np.float32().nbytes

        assert datafile_actual_size == datafile_expected_size
