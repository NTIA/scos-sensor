from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import ScheduleEntry


class CreateScheduleEntrySerializer(serializers.HyperlinkedModelSerializer):
    acquisitions = serializers.SerializerMethodField()

    class Meta:
        model = ScheduleEntry
        fields = (
            'url',
            'name',
            'action',
            'priority',
            'start',
            'stop',
            'relative_stop',
            'interval',
            'is_active',
            'next_task_time',
            'next_task_id',
            'created',
            'modified',
            'owner',
            'acquisitions'
        )
        extra_kwargs = {
            'url': {
                'view_name': 'v1:schedule-detail',
                'lookup_field': 'name'
            },
            'owner': {
                'view_name': 'v1:user-detail'
            }
        }
        read_only_fields = ('is_active',)
        write_only_fields = ('relative_stop',)

    def get_acquisitions(self, obj):
        request = self.context['request']
        kws = {'schedule_entry_name': obj.name}
        return reverse('v1:acquisition-list', kwargs=kws, request=request)

    def to_internal_value(self, data):
        """Strip incoming start=None so that model uses default start value."""
        if 'start' in data and data['start'] is None:
            data.pop('start')

        # py2.7 compat -> super().to_rep...
        cls = CreateScheduleEntrySerializer
        return super(cls, self).to_internal_value(data)


class UpdateScheduleEntrySerializer(CreateScheduleEntrySerializer):
    class Meta(CreateScheduleEntrySerializer.Meta):
        read_only_fields = ()  # allow changing 'is_active' after creation
