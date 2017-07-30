from rest_framework import serializers

from .models import ScheduleEntry


class ScheduleEntrySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ScheduleEntry
        fields = (
            'name',
            'action',
            'priority',
            'start',
            'stop',
            'relative_stop',
            'interval',
            'canceled',
            'created_at',
            'last_modified',
            'url'
        )
        extra_kwargs = {
            'url': {
                'view_name': 'v1:schedule-detail',
                'lookup_field': 'name'
            }
        }
