"""
Useful objects for generating OpenAPI documentation with drf_spectacular.
"""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiRequest, OpenApiResponse

# This set of keyword arguments is used to supply the extend_schema
# decorator with information about the "format" query parameter for
# function based views implemented with the api_view decorator. This
# provides information for the API documentation which cannot be obtained
# through introspection.

# See:
# https://www.django-rest-framework.org/api-guide/views/#function-based-views
# https://drf-spectacular.readthedocs.io/en/latest/drf_spectacular.html?highlight=extend_schema#drf_spectacular.utils.extend_schema
# https://drf-spectacular.readthedocs.io/en/latest/customization.html?highlight=extend_schema#step-2-extend-schema

FORMAT_QUERY_KWARGS = {
    "parameters": [
        OpenApiParameter(
            name="format",
            type=OpenApiTypes.STR,
            location="query",
            required=False,
            description=(
                "By default, the API returns HTML. "
                "This parameter allows for the return of raw JSON instead."
            ),
            enum=["json", "api"],
            allow_blank=True,
        )
    ],
    "request": OpenApiRequest("GET"),
    # auth = # TODO
}

API_RESPONSE_405 = {405: OpenApiResponse(description="Method Not Allowed")}


def view_docstring(docstring: str):
    """
    Overwrite the docstring of the decorated function.

    This decorator allows for a variable to be used the docstring
    for a function based view implemented with the api_view decorator.
    This allows for the same string to be used both in the web UI (where
    the docstring is used as the description text of the view) as well
    as in the OpenAPI documentation.

    Note that Markdown formatting is supported by Redoc, but will not
    be rendered in the web UI.

    :param docstring: The intended docstring for the decorated function.
    """

    def decorate(obj):
        obj.__doc__ = docstring
        return obj

    return decorate
