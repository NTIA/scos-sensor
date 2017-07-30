from rest_framework import serializers
from rest_framework.reverse import reverse

import actions


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
