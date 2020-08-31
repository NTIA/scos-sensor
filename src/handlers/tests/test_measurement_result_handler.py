import pytest
import numpy as np
from scos_actions.hardware.mocks.mock_radio import generate_random

from scos_actions.actions.interfaces.signals import measurement_action_completed
from tasks.models import Acquisition
from tasks.tests.utils import reverse_archive, simulate_timedomain_iq_acquisition, HTTPS_KWARG
from handlers.measurement_handler import measurement_action_completed_callback
import sensor
from rest_framework import status
import tempfile
import sigmf

class TestMeasurementResultHandler:

    def simulate_acq_get_data(self, user_client):
        _data = None
        _metadata = None
        _task_id = 0
        def handle(sender, **kwargs):
            nonlocal _data
            nonlocal _metadata
            nonlocal _task_id
            _task_id = kwargs["task_id"]
            _data = kwargs["data"]
            _metadata = kwargs["metadata"]

        measurement_action_completed.connect(handle)
        entry_name = simulate_timedomain_iq_acquisition(user_client)
        return entry_name, _task_id, _data

    def download_archive_data(self, user_client, entry_name, task_id):
        url = reverse_archive(entry_name, task_id)
        response = user_client.get(url, **HTTPS_KWARG)

        assert response.status_code == status.HTTP_200_OK

        archive_data = None
        with tempfile.NamedTemporaryFile() as tf:
            for content in response.streaming_content:
                tf.write(content)
            tf.flush()

            sigmf_archive_contents = sigmf.sigmffile.fromarchive(tf.name)
            md = sigmf_archive_contents._metadata
            archive_data = np.fromfile(sigmf_archive_contents.data_file, dtype=np.complex64)
        return archive_data

    @pytest.mark.django_db
    def test_measurement_result_handler_data_encrypted(self, settings, user_client, test_scheduler):
        settings.ENCRYPT_DATA_FILES = True
        entry_name, task_id, measurement_data = self.simulate_acq_get_data(user_client)
        
        acq = Acquisition.objects.get(task_result__schedule_entry__name=entry_name)
        assert acq.data_encrypted == True
        database_data = np.fromfile(acq.data, dtype=np.complex64)
        assert not np.array_equal(measurement_data, database_data)
        download_data = self.download_archive_data(user_client, entry_name, task_id)
        
        assert not np.array_equal(download_data, database_data)
        assert np.array_equal(measurement_data, download_data)

    @pytest.mark.django_db
    def test_measurement_result_handler_data_not_encrypted(self, settings, user_client, test_scheduler):
        settings.ENCRYPT_DATA_FILES = False
        entry_name, task_id, measurement_data = self.simulate_acq_get_data(user_client)

        acq = Acquisition.objects.get(task_result__schedule_entry__name=entry_name)
        assert acq.data_encrypted == False
        database_data = np.fromfile(acq.data, dtype=np.complex64)
        assert np.array_equal(measurement_data, database_data)
        download_data = self.download_archive_data(user_client, entry_name, task_id)
        
        assert np.array_equal(download_data, database_data)
        assert np.array_equal(measurement_data, download_data)
