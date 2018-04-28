from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import ModelViewSet

import actions
from .models import DEFAULT_PRIORITY, ScheduleEntry, Request
from .permissions import IsAdminOrOwnerOrReadOnly
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
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES + [
        IsAdminOrOwnerOrReadOnly,
    ]

    def create(self, request, *args, **kwargs):
        """Return NO CONTENT when input is valid but validate_only is True."""
        # https://github.com/encode/django-rest-framework/blob/master/
        # rest_framework/mixins.py#L18
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get('validate_only'):
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
        # .list() does not call .get_object(), which triggers permissions
        # checks, so we need to filter our queryset based on `is_private` and
        # request user.
        base_queryset = self.filter_queryset(self.queryset)
        if self.request.user.is_staff:
            return base_queryset.all()
        else:
            return base_queryset.filter(is_private=False)

    def get_serializer_class(self):
        """Modify the base serializer based on user and request."""

        updating = self.action in {'update', 'partial_update'}

        ro_fields = ()
        if updating:
            ro_fields += ('name',)
        else:
            ro_fields += ('is_active',)

        if not self.request.user.is_staff:
            ro_fields += ('is_private',)

        choices = actions.CHOICES
        if self.request.user.is_staff:
            choices += actions.ADMIN_CHOICES

        min_priority = 0
        if self.request.user.is_staff:
            min_priority = -20

        priority_help_text = "Lower number is higher priority (default={})"
        priority_help_text = priority_help_text.format(DEFAULT_PRIORITY)

        class Serializer(ScheduleEntrySerializer):
            action = serializers.ChoiceField(
                choices=choices,
                read_only=updating,
                help_text="[Required] The name of the action to be scheduled"
            )

            priority = serializers.IntegerField(
                required=False,
                allow_null=True,
                min_value=min_priority,
                max_value=19,
                help_text=priority_help_text
            )

            class Meta(ScheduleEntrySerializer.Meta):
                read_only_fields = ro_fields

        return Serializer
