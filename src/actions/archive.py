import logging

from django.core.files.base import ContentFile

from tasks.models import Acquisition, TaskResult

logger = logging.getLogger(__name__)


class Archive:
    def __call__(self, task_result_id, recording_id, acq_data, sigmf_md):
        task_result = TaskResult.object.get(id=task_result_id)

        logger.debug("Storing acquisition in database")

        name = task_result.schedule_entry.name + "_" + str(task_result.task_id)
        if recording_id:  # recording_id always starts with 1
            name += "_" + str(recording_id)
        name += ".sigmf-data"

        acquisition = Acquisition(
            task_result=task_result,
            recording_id=recording_id,
            metadata=sigmf_md._metadata,
        )
        acquisition.data.save(name, ContentFile(acq_data))
        acquisition.save()
        logger.debug("Saved new file at {}".format(acquisition.data.path))
