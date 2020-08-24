import pytest
import numpy as np
from scos_actions.hardware.mocks.mock_radio import generate_random

from scos_actions.actions.interfaces.signals import measurement_action_completed
from tasks.models import Acquisition
from tasks.tests.utils import simulate_timedomain_iq_acquisition

class TestMeasurementResultHandler:

    @pytest.mark.django_db
    def test_measurement_result_handler_data_encrypted(self, settings, user_client, test_scheduler):
        settings.ENCRYPT_DATA_FILES = True
        entry_name = simulate_timedomain_iq_acquisition(user_client)
        acq = Acquisition.objects.get(task_result__schedule_entry__name=entry_name)
        assert acq.data_encrypted == True

    @pytest.mark.django_db
    def test_measurement_result_handler_data_not_encrypted(self, settings, user_client, test_scheduler):
        settings.ENCRYPT_DATA_FILES = False
        entry_name = simulate_timedomain_iq_acquisition(user_client)
        acq = Acquisition.objects.get(task_result__schedule_entry__name=entry_name)
        assert acq.data_encrypted == False
