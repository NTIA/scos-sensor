import logging

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.files.base import ContentFile

from tasks.models import TaskResult

logger = logging.getLogger(__name__)


def measurement_action_completed_callback(sender, **kwargs):
    from tasks.models import Acquisition

    task_id = kwargs["task_id"]
    metadata = kwargs["metadata"]
    data = kwargs["data"]
    recording_id = None
    if "ntia-scos:recording" in metadata["global"]:
        recording_id = metadata["global"]["ntia-scos:recording"]

    logger.debug("Storing acquisition in database")

    schedule_entry_name = metadata["global"]["ntia-scos:schedule"]["name"]

    task_result = TaskResult.objects.get(
        schedule_entry__name=schedule_entry_name, task_id=task_id
    )

    name = schedule_entry_name + "_" + str(task_result.task_id)
    if recording_id:
        name += "_" + str(recording_id)
    name += ".sigmf-data"

    if recording_id:
        acquisition = Acquisition(
            task_result=task_result, metadata=metadata, recording_id=recording_id
        )
    else:
        acquisition = Acquisition(task_result=task_result, metadata=metadata)

    if settings.ENCRYPT_DATA_FILES:
        if not settings.ENCRYPTION_KEY:
            raise Exception("No value set for ENCRYPTION_KEY!")
        fernet = Fernet(settings.ENCRYPTION_KEY)
        _data = bytes(data)
        del data
        del kwargs["data"]
        assert "data" not in kwargs
        encrypted = fernet.encrypt(_data)
        del _data
        acquisition.data.save(name, ContentFile(encrypted))
        acquisition.data_encrypted = True
    else:
        acquisition.data.save(name, ContentFile(data))
        acquisition.data_encrypted = False
    acquisition.save()

    logger.debug(f"Saved new file at {acquisition.data.path}")
