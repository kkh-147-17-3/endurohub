from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        # Convert DRF validation errors to Laravel-compatible format
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            if isinstance(response.data, dict) and 'errors' not in response.data:
                response.data = {'errors': response.data}

    return response
