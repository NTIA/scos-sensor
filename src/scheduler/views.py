from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet

from . import scheduler
from .models import ScheduleEntry
from .serializers import ScheduleEntrySerializer, TaskSerializer


class ScheduleEntryViewSet(ModelViewSet):
    queryset = ScheduleEntry.objects.filter(canceled=False)
    serializer_class = ScheduleEntrySerializer
    lookup_field = 'name'


class SchedulerViewSet(ViewSet):
    def list(self, request, format=None):
        queue = scheduler.thread.task_queue.to_list()
        context = {'request': request}
        serializer = TaskSerializer(queue, many=True, context=context)
        return Response({
            'status': 'running' if scheduler.thread.running else 'idle',
            'task_queue': serializer.data
        })
