from drf_openapi.codec import OpenAPIRenderer, SwaggerUIRenderer
from drf_openapi.entities import OpenApiSchemaGenerator
from rest_framework import response, permissions
from rest_framework.views import APIView

from .settings import API_TITLE, API_DESCRIPTION


class SchemaView(APIView):
    """The schema overview for the API."""
    renderer_classes = (SwaggerUIRenderer, OpenAPIRenderer)
    permission_classes = (permissions.IsAuthenticated, )
    url = ''

    def get(self, request, version):
        generator = OpenApiSchemaGenerator(
            version=version,
            url=self.url,
            title=API_TITLE,
            description=API_DESCRIPTION,
        )

        return response.Response(generator.get_schema(request))
