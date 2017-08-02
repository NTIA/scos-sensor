from rest_framework import serializers
from rest_framework.reverse import reverse

from schedule.models import ScheduleEntry
from .models import Acquisition


class AcquisitionsOverviewSerializer(serializers.HyperlinkedModelSerializer):
    schedule_entry_name = serializers.SerializerMethodField()
    acquisitions_available = serializers.SerializerMethodField()
    schedule_entry_url = serializers.SerializerMethodField()

    class Meta:
        model = ScheduleEntry
        fields = (
            'schedule_entry_name',
            'acquisitions_available',
            'created_at',
            'schedule_entry_url',
            'url'
        )
        extra_kwargs = {
            'url': {
                'view_name': 'v1:acquisitions-detail',
                'lookup_field': 'name',
                'lookup_url_kwarg': 'schedule_entry_name'
            }
        }

    def get_schedule_entry_name(self, obj):
        return obj.name

    def get_acquisitions_available(self, obj):
        return obj.acquisitions.count()

    def get_schedule_entry_url(self, obj):
        request = self.context['request']
        return reverse('v1:schedule-detail',
                       args=(obj.name,),
                       request=request)


class AcquisitionHyperlinkedRelatedField(serializers.HyperlinkedRelatedField):
    # http://www.django-rest-framework.org/api-guide/relations/#custom-hyperlinked-fields

    def get_url(self, obj, view_name, request, format):
        kw = {
            'schedule_entry_name': obj.schedule_entry.name,
            'task_id': obj.task_id
        }
        return reverse(view_name, kwargs=kw, request=request, format=format)


class AcquisitionSerializer(serializers.Serializer):
    metadata = AcquisitionHyperlinkedRelatedField(
        view_name='v1:acquisition-metadata',
        read_only=True,
        source='*'  # pass whole object
    )
    data = AcquisitionHyperlinkedRelatedField(
        view_name='v1:acquisition-data',
        read_only=True,
        source='*'  # pass whole object
    )

    class Meta:
        model = Acquisition
        fields = '__all__'
