import logging

from django.http import Http404

from rest_framework import serializers
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework.exceptions import APIException, PermissionDenied

from .responses import error_response

logger = logging.getLogger(__name__)


def custom_exception_handler(exception, context) -> Response | None:
    if not isinstance(exception, serializers.ValidationError | Http404 | PermissionDenied):
        logger.exception(
            'An exception occurred while handling request %s',
            context['request'].get_full_path(),
            exc_info=exception,
        )

    response = exception_handler(exception, context)
    if response is None:
        return None

    if isinstance(exception, APIException):
        return error_response(
            error=[exception.detail] if isinstance(exception.detail, str) else exception.detail,
            status_code=response.status_code,
        )

    return error_response(error=str(exception), status_code=response.status_code)
