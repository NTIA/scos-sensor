from rest_framework import serializers
from rest_framework.reverse import reverse

import actions
from sensor import V1


class TaskSerializer(serializers.Serializer):
    schedule_entry = serializers.SerializerMethodField()
    action = serializers.CharField(max_length=actions.MAX_LENGTH)
    priority = serializers.IntegerField()
    time = serializers.IntegerField()

    def get_schedule_entry(self, obj):
        request = self.context['request']
        kws = {'pk': obj.schedule_entry_name}
        kws.update(V1)
        return reverse('schedule-detail', kwargs=kws, request=request)
