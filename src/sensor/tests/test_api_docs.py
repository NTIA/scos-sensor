import json

import pytest
from rest_framework.reverse import reverse

from sensor import V1, settings


@pytest.mark.update_api_docs
def test_api_docs_up_to_date(admin_client):
    """Ensure that docs/openapi.json is up-to-date."""
    schema_url = reverse('api_schema', kwargs=V1)
    response = admin_client.get(schema_url)
    with open(settings.OPENAPI_FILE, 'w') as openapi_file:
        openapi_json = json.loads(response.content)
        json.dump(openapi_json, openapi_file, indent=4)
