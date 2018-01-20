from rest_framework import serializers
from rest_framework.reverse import reverse

import actions
from sensor import V1
from .models import ScheduleEntry


class CreateScheduleEntrySerializer(serializers.HyperlinkedModelSerializer):
    acquisitions = serializers.SerializerMethodField(
        help_text="The list of acquisitions related to the entry"
    )
    results = serializers.SerializerMethodField(
        help_text="The list of results related to the entry"
    )
    stop_is_relative = serializers.BooleanField(
        required=False,
        help_text=("Indicates that the `stop` field should be interpreted as "
                   "seconds after `start` instead of an absolute time")
    )
    action = serializers.ChoiceField(
        choices=actions.CHOICES,
        help_text="The name of the action to be scheduled"
    )

    class Meta:
        model = ScheduleEntry
        fields = (
            'url',
            'name',
            'action',
            'priority',
            'start',
            'stop',
            'stop_is_relative',
            'interval',
            'is_active',
            'is_private',
            'callback_url',
            'next_task_time',
            'next_task_id',
            'created',
            'modified',
            'owner',
            'acquisitions',
            'results'
        )
        extra_kwargs = {
            'url': {
                'view_name': 'schedule-detail',
                'help_text': "The url of the entry"
            },
            'owner': {
                'view_name': 'user-detail',
                'help_text': "The name of the user who owns the entry"
            }
        }
        read_only_fields = ('is_active', 'is_private')
        write_only_fields = ('stop_is_relative',)

    def get_acquisitions(self, obj):
        request = self.context['request']
        kws = {'schedule_entry_name': obj.name}
        kws.update(V1)
        return reverse('acquisition-list', kwargs=kws, request=request)

    def get_results(self, obj):
        request = self.context['request']
        kws = {'schedule_entry_name': obj.name}
        kws.update(V1)
        return reverse('result-list', kwargs=kws, request=request)

    def to_internal_value(self, data):
        """Strip incoming start=None so that model uses default start value."""
        if 'start' in data and data['start'] is None:
            data.pop('start')

        # Hack: scheduler needs to have _some_ request context to reverse URLs
        from scheduler import scheduler
        scheduler.thread.request = self.context['request']

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
