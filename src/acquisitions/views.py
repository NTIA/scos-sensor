from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from schedule.models import ScheduleEntry
from .models import Acquisition
from .serializers import AcquisitionSerializer, AcquisitionsOverviewSerializer


class AcquisitionViewSet(ViewSet):
    def list(self, request):
        queryset = ScheduleEntry.objects.all()
        context = {'request': request}
        serializer = AcquisitionsOverviewSerializer(queryset,
                                                    many=True,
                                                    context=context)
        return Response(serializer.data)

    def retrieve(self, request, entry_name):
        queryset = ScheduleEntry.objects.all()
        entry = get_object_or_404(queryset, name=entry_name)
        serializer = AcquisitionSerializer(entry.acquisitions, many=True)
        return Response(serializer.data)

    def destroy(self, request, entry_name):
        raise NotImplemented
