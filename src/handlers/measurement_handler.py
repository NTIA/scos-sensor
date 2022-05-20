from cryptography.fernet import Fernet
import logging

from django.core.files.base import ContentFile

from tasks.models import TaskResult
from django.conf import settings

ENCRYPTION_KEY = settings.ENCRYPTION_KEY

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
        if not ENCRYPTION_KEY:
            raise Exception("No value set for ENCRYPTION_KEY!")
        fernet = Fernet(ENCRYPTION_KEY)
        encrypted = fernet.encrypt(bytes(data))
        acquisition.data.save(name, ContentFile(encrypted))
        acquisition.data_encrypted = True
    else:
        acquisition.data.save(name, ContentFile(data))
        acquisition.data_encrypted = False
    acquisition.save()
    
    logger.debug("Saved new file at {}".format(acquisition.data.path))
