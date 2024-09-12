from typing import Any

from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.response import Response


def success_response(data: Any, status_code: int = HTTP_200_OK) -> Response:
    """Generate a success response with the provided data and status code."""
    return Response({'success': True, 'data': data}, status=status_code)


def error_response(error: Any, status_code: int = HTTP_400_BAD_REQUEST) -> Response:
    """Generate an error response with the provided message, error, and status code."""
    error_data = {'error': error, 'success': False}
    return Response(error_data, status=status_code)
