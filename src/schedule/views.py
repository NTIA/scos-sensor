from rest_framework import filters, status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import ModelViewSet

from .models import Request, ScheduleEntry
from .serializers import ScheduleEntrySerializer


class ScheduleEntryViewSet(ModelViewSet):
    """View and modify the schedule.

    list:
    Retrieves the current schedule.

    create:
    Creates a new schedule entry.

    retrieve:
    Returns the specified schedule entry.

    update:
    Updates the specified schedule entry.

    partial_update:
    Partially updates the specified schedule entry.

    delete:
    Deletes the specified schedule entry.

    """

    queryset = ScheduleEntry.objects.all()
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    lookup_fields = ("schedule_entry__name", "task_id")
    ordering_fields = ("priority", "start", "next_task_time", "created", "modified")
    search_fields = ("name", "action")

    def create(self, request, *args, **kwargs):
        """Return NO CONTENT when input is valid but validate_only is True."""
        # https://github.com/encode/django-rest-framework/blob/master/
        # rest_framework/mixins.py#L18
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get("validate_only"):
            return Response(status=status.HTTP_204_NO_CONTENT)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        created = status.HTTP_201_CREATED
        return Response(serializer.data, status=created, headers=headers)

    def perform_create(self, serializer):
        r = Request()
        r.from_drf_request(self.request)
        serializer.save(request=r, owner=self.request.user)

    def get_queryset(self):
        # .list() does not call .get_object()
        base_queryset = self.filter_queryset(self.queryset)
        return base_queryset.all()

    def get_serializer_class(self):
        """Modify the base serializer based on user and request."""

        updating = self.action in {"update", "partial_update"}

        SerializerBaseClass = ScheduleEntrySerializer

        ro_fields = SerializerBaseClass.Meta.read_only_fields

        if updating:
            ro_fields += ("name", "action")
        else:
            ro_fields += ("is_active",)

        class SerializerClass(SerializerBaseClass):
            class Meta(SerializerBaseClass.Meta):
                read_only_fields = ro_fields

        return SerializerClass
