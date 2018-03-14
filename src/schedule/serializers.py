from datetime import datetime

from rest_framework import serializers
from rest_framework.reverse import reverse

import actions
from sensor import V1
from .models import ScheduleEntry


class ScheduleEntrySerializer(serializers.HyperlinkedModelSerializer):
    acquisitions = serializers.SerializerMethodField(
        help_text="The list of acquisitions related to the entry"
    )
    results = serializers.SerializerMethodField(
        help_text="The list of results related to the entry"
    )
    start = serializers.DateTimeField(
        required=False,
        help_text="UTC time (ISO 8601) to start, or leave blank for 'now'"
    )
    absolute_stop = serializers.DateTimeField(
        required=False,
        help_text=("UTC time (ISO 8601) to stop, "
                   "or leave blank for 'never' (not valid with relative_stop)")
    )
    relative_stop = serializers.IntegerField(
        required=False,
        help_text=("Integer seconds after start to stop, "
                   "or leave blank for 'never' (not valid with absolute_stop)")
    )
    next_task_time = serializers.SerializerMethodField(
        help_text="UTC time (ISO 8601) the next task is scheduled for"
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
            'absolute_stop',
            'relative_stop',
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
        read_only_fields = ('is_active', 'is_private', 'next_task_time',
                            'stop')
        write_only_fields = ('absolute_stop', 'relative_stop',)

    def validate(self, data):
        """Do object-level validation."""
        got_absolute_stop = False
        got_relative_stop = False

        if 'absolute_stop' in data and data['absolute_stop'] is not None:
            got_absolute_stop = True

        if 'relative_stop' in data and data['relative_stop'] is not None:
            got_relative_stop = True

        if got_absolute_stop and got_relative_stop:
            err = "pass only one of absolute_stop and relative_stop"
            raise serializers.ValidationError(err)

        return data

    def get_absolute_stop(self, obj):
        return datetime.fromtimestamp(obj.stop)

    def get_acquisitions(self, obj):
        request = self.context['request']
        kws = {'schedule_entry_name': obj.name}
        kws.update(V1)
        return reverse('acquisition-list', kwargs=kws, request=request)

    def get_next_task_time(self, obj):
        return datetime.fromtimestamp(obj.next_task_time)

    def get_results(self, obj):
        request = self.context['request']
        kws = {'schedule_entry_name': obj.name}
        kws.update(V1)
        return reverse('result-list', kwargs=kws, request=request)

    def to_internal_value(self, data):
        """Strip incoming start=None so that model uses default start value."""
        if 'start' in data and data['start'] is None:
            data.pop('start')

        # py2.7 compat -> super().to_internal...
        return super(ScheduleEntrySerializer, self).to_internal_value(data)

    def to_representation(self, obj):
        """Translate Unix timestamps to datetime format."""
        obj.start = datetime.fromtimestamp(obj.start)

        # py2.7 compat -> super().to_internal...
        return super(ScheduleEntrySerializer, self).to_representation(obj)
