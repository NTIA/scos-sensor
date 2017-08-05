from rest_framework import serializers
from rest_framework.reverse import reverse

import actions


class TaskSerializer(serializers.Serializer):
    schedule_entry = serializers.SerializerMethodField()
    action = serializers.CharField(max_length=actions.MAX_LENGTH)
    priority = serializers.IntegerField()
    time = serializers.IntegerField()

    def get_schedule_entry(self, obj):
        request = self.context['request']
        return reverse('v1:schedule-detail',
                       args=(obj.schedule_entry_name,),
                       request=request)
