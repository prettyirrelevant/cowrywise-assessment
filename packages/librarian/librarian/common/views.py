from django.http import HttpRequest, JsonResponse

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import status, permissions
from drf_yasg.generators import OpenAPISchemaGenerator


def handler_400(request, exception, *args, **kwargs):  # noqa: ARG001
    return JsonResponse(
        data={'error': 'Bad request', 'success': False},
        status=status.HTTP_400_BAD_REQUEST,
    )


def handler_404(request, exception):  # noqa: ARG001
    return JsonResponse(data={'error': 'Not found', 'success': False}, status=status.HTTP_404_NOT_FOUND)


def handler_500(request: HttpRequest) -> JsonResponse:  # noqa: ARG001
    return JsonResponse(
        data={
            'error': "We're sorry, but something went wrong on our end",
            'success': False,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


class HttpAndHttpsOpenAPISchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):  # noqa: FBT002
        schema = super().get_schema(request, public)
        schema.schemes = ['http', 'https']
        return schema


schema_view = get_schema_view(
    openapi.Info(
        title='Librarian API',
        default_version='v1',
        license=openapi.License(name='MIT License'),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    generator_class=HttpAndHttpsOpenAPISchemaGenerator,
)
