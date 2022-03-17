import pytest
from django import conf
from status.models import  Location
from scos_actions.capabilities import capabilities

@pytest.mark.django_db
def test_db_location_update_handler():
    capabilities['sensor'] ={}
    capabilities['sensor']['location'] = {}
    location = Location()
    location.gps = False
    location.height=10
    location.longitude = 100
    location.latitude = -1
    location.description = 'test'
    location.save()
    assert capabilities['sensor']['location']['x'] == 100
    assert capabilities['sensor']['location']['y'] == -1
    assert capabilities['sensor']['location']['z'] == 10
    assert capabilities['sensor']['location']['description'] == 'test'

@pytest.mark.django_db
def test_db_location_update_handler_no_description():
    capabilities['sensor'] ={}
    capabilities['sensor']['location'] = {}
    location = Location()
    location.gps = False
    location.height=10
    location.longitude = 100
    location.latitude = -1
    location.save()
    assert capabilities['sensor']['location']['x'] == 100
    assert capabilities['sensor']['location']['y'] == -1
    assert capabilities['sensor']['location']['z'] == 10
    assert capabilities['sensor']['location']['description'] == ''


@pytest.mark.django_db
def test_db_location_deleted_handler():
    capabilities['sensor'] ={}
    capabilities['sensor']['location'] = {}
    location = Location()
    location.gps = False
    location.height=10
    location.longitude = 100
    location.latitude = -1
    location.description = 'test'
    location.active = True
    location.save()
    assert capabilities['sensor']['location']['x'] == 100
    assert capabilities['sensor']['location']['y'] == -1
    assert capabilities['sensor']['location']['z'] == 10
    assert capabilities['sensor']['location']['description'] == 'test'
    location.delete()
    assert capabilities['sensor']['location'] is None

@pytest.mark.django_db
def test_db_location_deleted_inactive_handler():
    capabilities['sensor'] ={}
    capabilities['sensor']['location'] = {}
    location = Location()
    location.gps = False
    location.height=10
    location.longitude = 100
    location.latitude = -1
    location.description = 'test'
    location.active = False
    location.save()
    assert capabilities['sensor']['location']['x'] == 100
    assert capabilities['sensor']['location']['y'] == -1
    assert capabilities['sensor']['location']['z'] == 10
    assert capabilities['sensor']['location']['description'] == 'test'
    location.delete()
    assert capabilities['sensor']['location']['x'] == 100
    assert capabilities['sensor']['location']['y'] == -1
    assert capabilities['sensor']['location']['z'] == 10
    assert capabilities['sensor']['location']['description'] == 'test'