from collections import namedtuple
from unittest.mock import patch

import pytest

from tasks.models import TaskResult
from tasks.tests.utils import create_task_results, simulate_frequency_fft_acquisitions
from django.conf import settings

DiskUsage = namedtuple('DiskUsage', ['total', 'used', 'free'])

@pytest.mark.django_db
def test_max_disk_usage_under_over_limit(admin_client, test_scheduler):
    """If disk usage is too high, oldest task result of current schedule_entry should be deleted"""
    with patch("tasks.models.task_result.shutil") as mock_shutil:
        usage = (settings.MAX_DISK_USAGE / 100)*500e9/2
        mock_shutil.disk_usage.return_value = DiskUsage(total=500e9, used=usage, free=500e9-usage)
        simulate_frequency_fft_acquisitions(admin_client, 10)
        assert TaskResult.objects.count() == 10

        usage = ((settings.MAX_DISK_USAGE + (100 - settings.MAX_DISK_USAGE)/2) / 100) * 500e9
        mock_shutil.disk_usage.return_value = DiskUsage(total=500e9, used=usage, free=500e9 - usage)
        simulate_frequency_fft_acquisitions(admin_client, 10, name="part2")
        assert TaskResult.objects.count() == 11
        assert TaskResult.objects.all()[10].id == 20 # make sure most recent result kept

@pytest.mark.django_db
def test_max_disk_usage_over_under_limit(admin_client, test_scheduler):
    """If disk usage is too high, oldest task result of current schedule_entry should be deleted"""
    with patch("tasks.models.task_result.shutil") as mock_shutil:
        usage = ((settings.MAX_DISK_USAGE + (100 - settings.MAX_DISK_USAGE)/2) / 100) * 500e9
        mock_shutil.disk_usage.return_value = DiskUsage(total=500e9, used=usage, free=500e9 - usage)
        simulate_frequency_fft_acquisitions(admin_client, 10)
        assert TaskResult.objects.count() == 1
        assert TaskResult.objects.all()[0].id == 10 # make sure most recent result kept

        usage = (settings.MAX_DISK_USAGE / 100)*500e9/2
        mock_shutil.disk_usage.return_value = DiskUsage(total=500e9, used=usage, free=500e9 - usage)
        simulate_frequency_fft_acquisitions(admin_client, 10, name="part2")
        assert TaskResult.objects.count() == 11

@pytest.mark.django_db
def test_str(admin_client):
    create_task_results(1, admin_client)
    str(TaskResult.objects.get())
