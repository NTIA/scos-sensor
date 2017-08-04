import pytest
from rest_framework import status

from acquisitions.tests import SINGLE_ACQUISITION, EMPTY_ACQUISITIONS_RESPONSE
from acquisitions.tests.utils import (reverse_acquisitions_overview,
                                      reverse_acquisition_list,
                                      simulate_acquisitions,
                                      get_acquisitions_overview)
from schedule.tests.utils import post_schedule
from sensor.tests.utils import validate_response


@pytest.mark.django_db
def test_empty_overview_response(client):
    assert get_acquisitions_overview(client) == EMPTY_ACQUISITIONS_RESPONSE


@pytest.mark.django_db
def test_overview_exists_when_entry_created(client, testclock):
    post_schedule(client, SINGLE_ACQUISITION)
    overview, = get_acquisitions_overview(client)
    assert overview['acquisitions_available'] == 0


@pytest.mark.django_db
def test_get_overview(client, testclock):
    entry1_name = simulate_acquisitions(client, n=1)
    overview, = get_acquisitions_overview(client)
    assert overview['url'] == reverse_acquisition_list(entry1_name)
    assert overview['acquisitions_available'] == 1
    entry2_name = simulate_acquisitions(client, n=3)
    overview_list = get_acquisitions_overview(client)
    assert len(overview_list) == 2
    (overview1, overview2) = overview_list
    assert overview1 == overview
    assert overview2['url'] == reverse_acquisition_list(entry2_name)
    assert overview2['acquisitions_available'] == 3


@pytest.mark.django_db
def test_delete_overview_not_allowed(client, testclock):
    url = reverse_acquisitions_overview()
    assert validate_response(client.delete(url),
                             status.HTTP_405_METHOD_NOT_ALLOWED)
