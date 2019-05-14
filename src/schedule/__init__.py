"""Initialize schedule state from YAML config files."""

import logging
from pathlib import Path

from rest_framework.serializers import ValidationError
from ruamel.yaml import YAML

from sensor import settings


logger = logging.getLogger(__name__)


def load_from_yaml(yaml_dir=settings.SCHEDULE_ENTRIES_DIR):
    """Load any YAML files in yaml_dir."""

    import actions
    from authentication.models import User
    from schedule.models import ScheduleEntry
    from schedule.serializers import ScheduleEntrySerializer

    yaml = YAML(typ='safe')
    yaml_path = Path(yaml_dir)
    for yaml_file in yaml_path.glob('*.yml'):
        entry = yaml.load(yaml_file)
        for name, parameters in entry.items():
            if ScheduleEntry.objects.filter(name=name):
                msg = "Entry with name {!r} already exists in schedule"
                msg += ", skipping"
                logger.info(msg.format(name))
                continue

            parameters['name'] = name

            # if 'callback_url' in parameters:
            #     err = "`callback_url` cannot be used with the YAML-loader. "
            #     err += "Generating the TaskResult that is sent to the "
            #     err += "callback_url requires a request context."
            #     logger.error(err)
            #     raise RuntimeError(err)

            try:
                username = parameters.pop('owner')
                owner = User.objects.get(username=username)
            except KeyError as exc:
                err = "Required key 'owner' not specified in {!r}"
                logger.error(err.format(yaml_file.name))
                logger.exception(exc)
                raise exc
            except User.DoesNotExist as exc:
                err = "Owner {!r} referenced in {!r} does not exist"
                logger.error(err.format(username, yaml_file.name))
                logger.exception(exc)
                raise exc

            choices = actions.CHOICES
            if owner.is_staff:
                choices += actions.ADMIN_CHOICES

            deserializer = ScheduleEntrySerializer(data=parameters)
            try:
                deserializer.is_valid(raise_exception=True)
            except ValidationError as exc:
                err = "Invalid schedule entry parameters specified in {!r}"
                logger.error(err.format(yaml_file.name))
                logger.exception(exc)
                raise exc

            deserializer.save(request=None, owner=owner)


def init():
    """Run schedule initialization routines."""
    load_from_yaml()
