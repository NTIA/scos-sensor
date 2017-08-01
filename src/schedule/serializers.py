from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import ScheduleEntry


class ScheduleEntrySerializer(serializers.HyperlinkedModelSerializer):
    acquisitions_url = serializers.SerializerMethodField()

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
            'acquisitions_url',
            'url'
        )
        extra_kwargs = {
            'url': {
                'view_name': 'v1:schedule-detail',
                'lookup_field': 'name'
            }
        }

    def get_acquisitions_url(self, obj):
        request = self.context['request']
        return reverse('v1:acquisitions-detail',
                       args=(obj.name,),
                       request=request)
