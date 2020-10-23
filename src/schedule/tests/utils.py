import json
from itertools import chain

from rest_framework import status
from rest_framework.reverse import reverse

from sensor import V1

EMPTY_SCHEDULE_RESPONSE = []

TEST_SCHEDULE_ENTRY = {"name": "test", "action": "logger"}

TEST_ALTERNATE_SCHEDULE_ENTRY = {
    "name": "test_alternate",
    "action": "logger",
    "priority": 5,
}

TEST_PRIVATE_SCHEDULE_ENTRY = {
    "name": "test_private",
    "action": "logger",
}


def post_schedule(client, entry, expected_status=status.HTTP_201_CREATED):
    kwargs = {
        "data": json.dumps(entry),
        "content_type": "application/json",
        "secure": True,
        "wsgi.url_scheme": "https",
    }

    url = reverse("schedule-list", kwargs=V1)
    r = client.post(url, **kwargs)

    err = "Got status {}, expected {}".format(r.status_code, expected_status)
    assert r.status_code == expected_status, err

    if r.status_code == status.HTTP_204_NO_CONTENT:
        return None

    return r.json()


def update_schedule(client, entry_name, new_entry):
    url = reverse_detail_url(entry_name)

    kwargs = {
        "data": json.dumps(new_entry),
        "content_type": "application/json",
        "secure": True,
        "wsgi.url_scheme": "https",
    }

    return client.put(url, **kwargs)


def reverse_detail_url(entry_name):
    kws = {"pk": entry_name}
    kws.update(V1)
    url = reverse("schedule-detail", kwargs=kws)
    return url


# https://docs.python.org/3/library/itertools.html#itertools-recipes
def flatten(list_of_lists):
    """Flatten one level of nesting."""
    return chain.from_iterable(list_of_lists)
