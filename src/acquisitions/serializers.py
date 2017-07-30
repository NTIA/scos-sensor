from rest_framework import serializers
from rest_framework.reverse import reverse

from schedule.models import ScheduleEntry
from .models import Acquisition


class AcquisitionsOverviewSerializer(serializers.HyperlinkedModelSerializer):
    nacquisitions = serializers.SerializerMethodField()
    schedule_entry_url = serializers.SerializerMethodField()

    class Meta:
        model = ScheduleEntry
        fields = (
            'name',
            'created_at',
            'nacquisitions',
            'schedule_entry_url'
        )

    def get_nacquisitions(self, obj):
        return obj.acquisitions.count()

    def get_schedule_entry_url(self, obj):
        request = self.context['request']
        return reverse('v1:schedule-detail',
                       args=(obj.name,),
                       request=request)


class AcquisitionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Acquisition
        fields = '__all__'
