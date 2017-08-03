import json
from itertools import chain

from rest_framework import status
from rest_framework.reverse import reverse


def post_schedule(client, entry):
    r = client.post(reverse('v1:schedule-list'),
                    data=json.dumps(entry),
                    content_type='application/json')
    rjson = r.json()
    assert r.status_code == status.HTTP_201_CREATED, rjson
    return rjson


# https://docs.python.org/3/library/itertools.html#itertools-recipes
def flatten(list_of_lists):
    "Flatten one level of nesting"
    return chain.from_iterable(list_of_lists)
