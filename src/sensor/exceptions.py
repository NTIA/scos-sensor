"""Provides custom exception handing."""

from __future__ import absolute_import

import logging

from django import db
from django.db.models.deletion import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import exception_handler as default_exception_handler


logger = logging.getLogger(__name__)


def exception_handler(exc, context):
    # Get the standard error response
    response = default_exception_handler(exc, context)

    if response is None:
        if isinstance(exc, ProtectedError):
            response = handle_protected_error(exc, context)
        elif isinstance(exc, db.IntegrityError):
            response = Response({
                'detail': str(exc)
            }, status=status.HTTP_409_CONFLICT)
        else:
            logger.exception("Caught unhandled exception", exc_info=exc)

    return response


def handle_protected_error(exc, context):
    if 'name' in context['kwargs']:
        entry_name = context['kwargs']['name']
    else:
        entry_name = context['kwargs']['pk']

    request = context['request']

    protected_object_urls = []
    for protected_object in exc.protected_objects:
        task_id = protected_object.task_id
        url_kwargs = {
            'schedule_entry_name': entry_name,
            'task_id': task_id
        }
        view_name = 'v1:acquisition-detail'
        url = reverse(view_name, kwargs=url_kwargs, request=request)
        protected_object_urls.append(url)

    response = Response({
        'detail': (
            "Cannot delete schedule entry {!r} because acquisitions on disk "
            "reference it. Delete the protected acquisitions first."
        ).format(entry_name),
        'protected_objects': protected_object_urls
    }, status=status.HTTP_400_BAD_REQUEST)

    return response
