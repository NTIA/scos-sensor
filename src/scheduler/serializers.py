from rest_framework import serializers
from rest_framework.reverse import reverse

import actions
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


class TaskSerializer(serializers.Serializer):
    schedule_entry_name = serializers.SlugField()
    schedule_entry_url = serializers.SerializerMethodField()
    task_id = serializers.IntegerField(write_only=True)
    action = serializers.CharField(max_length=actions.MAX_LENGTH)
    priority = serializers.IntegerField()
    time = serializers.IntegerField()

    def get_schedule_entry_url(self, obj):
        request = self.context['request']
        return reverse('v1:schedule-detail',
                       args=(obj.schedule_entry_name,),
                       request=request)
