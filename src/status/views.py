from rest_framework.decorators import api_view
from rest_framework.response import Response

from scheduler import scheduler
from scheduler.serializers import TaskSerializer


@api_view()
def status(request, format=None):
    context = {'request': request}
    taskq = scheduler.thread.task_queue.to_list()
    task_serializer = TaskSerializer(taskq, many=True, context=context)

    return Response({
        'scheduler': scheduler.thread.status,
        'task_queue': task_serializer.data
    })
