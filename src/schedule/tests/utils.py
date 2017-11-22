import json
from itertools import chain

from rest_framework import status
from rest_framework.reverse import reverse


def post_schedule(client, entry):
    kwargs = {
        'data': json.dumps(entry),
        'content_type': 'application/json',
        'wsgi.url_scheme': 'https'
    }

    r = client.post(reverse('v1:schedule-list'), **kwargs)
    rjson = r.json()

    assert r.status_code == status.HTTP_201_CREATED, rjson

    return rjson


def update_schedule(client, entry_name, new_entry):
    url = reverse('v1:schedule-detail', [entry_name])

    kwargs = {
        'data': json.dumps(new_entry),
        'content_type': 'application/json',
        'wsgi.url_scheme': 'https'
    }

    return client.put(url, **kwargs)


# https://docs.python.org/3/library/itertools.html#itertools-recipes
def flatten(list_of_lists):
    "Flatten one level of nesting"
    return chain.from_iterable(list_of_lists)
