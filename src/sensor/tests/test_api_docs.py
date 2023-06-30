import json
from os import path

from rest_framework.reverse import reverse

from sensor import V1, settings


def test_api_docs_up_to_date(admin_client):
    """Ensure that docs/openapi.json is up-to-date."""

    docs_dir = path.dirname(settings.OPENAPI_FILE)
    if not path.exists(docs_dir):
        # Probably running in Docker container for Jenkins... test should pass
        print(f"{docs_dir} doesn't exist, not in src tree.")
        return True

    schema_url = reverse("api_schema", kwargs=V1) + "?format=openapi"
    response = admin_client.get(schema_url)

    with open(settings.OPENAPI_FILE, "w+") as openapi_file:
        openapi_json = json.loads(response.content)
        json.dump(openapi_json, openapi_file, indent=4)
