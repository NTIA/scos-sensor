from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet

from . import scheduler
from .models import ScheduleEntry
from .serializers import ScheduleEntrySerializer, TaskSerializer


class ScheduleEntryViewSet(ModelViewSet):
    queryset = ScheduleEntry.objects.all()
    serializer_class = ScheduleEntrySerializer


class SchedulerViewSet(ViewSet):
    def list(self, request, format=None):
        queue = scheduler.thread.task_queue.to_list()
        serializer = TaskSerializer(queue,
                                    many=True,
                                    context={'request': request})
        return Response({
            'status': 'running' if scheduler.thread.running else 'idle',
            'task_queue': serializer.data
        })
