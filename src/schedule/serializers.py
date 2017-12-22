from rest_framework import serializers
from rest_framework.reverse import reverse

import actions
from sensor import V1
from .models import ScheduleEntry


class CreateScheduleEntrySerializer(serializers.HyperlinkedModelSerializer):
    acquisitions = serializers.SerializerMethodField()
    relative_stop = serializers.BooleanField(required=False)
    action = serializers.ChoiceField(choices=actions.CHOICES)

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
            'is_private',
            'next_task_time',
            'next_task_id',
            'created',
            'modified',
            'owner',
            'acquisitions'
        )
        extra_kwargs = {
            'url': {
                'view_name': 'schedule-detail'
            },
            'owner': {
                'view_name': 'user-detail'
            }
        }
        read_only_fields = ('is_active', 'is_private')
        write_only_fields = ('relative_stop',)

    def get_acquisitions(self, obj):
        request = self.context['request']
        kws = {'schedule_entry_name': obj.name}
        kws.update(V1)
        return reverse('acquisition-list', kwargs=kws, request=request)

    def to_internal_value(self, data):
        """Strip incoming start=None so that model uses default start value."""
        if 'start' in data and data['start'] is None:
            data.pop('start')

        # py2.7 compat -> super().to_internal...
        cls = CreateScheduleEntrySerializer
        return super(cls, self).to_internal_value(data)


class AdminCreateScheduleEntrySerializer(CreateScheduleEntrySerializer):
    action = serializers.ChoiceField(
        choices=(actions.CHOICES + actions.ADMIN_CHOICES)
    )

    class Meta(CreateScheduleEntrySerializer.Meta):
        read_only_fields = ('is_active',)  # allow setting 'is_private'


class UpdateScheduleEntrySerializer(CreateScheduleEntrySerializer):
    class Meta(CreateScheduleEntrySerializer.Meta):
        # allow changing 'is_active' after creation
        read_only_fields = ('name',)
