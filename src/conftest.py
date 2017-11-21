import pytest
from django.test.client import Client

import actions
import actions.tests.mocks.usrp
import scheduler
from authentication.models import User


def pytest_addoption(parser):
    parser.addoption("--testlive", action="store_true",
                     help="also run deterministic tests on live system")


@pytest.fixture
def testlive(request):
    return request.config.getoption("--testlive")


@pytest.yield_fixture
def testclock():
    real_timefn = scheduler.scheduler.utils.timefn
    real_delayfun = scheduler.utils.delayfn
    scheduler.utils.timefn = scheduler.tests.utils.TestClock()
    scheduler.utils.delayfn = scheduler.tests.utils.delayfn
    yield scheduler.utils.timefn
    scheduler.utils.timefn = real_timefn
    scheduler.utils.delayfn = real_delayfun


@pytest.fixture
def user(db):
    """A normal user."""
    username = 'test'
    password = 'password'

    user, created = User.objects.get_or_create(username=username)

    if created:
        user.set_password(password)
        user.save()

    user.password = password

    return user


@pytest.fixture
def user_client(db, user):
    """A Django test client logged in as a normal user"""
    client = Client()
    client.login(username=user.username, password=user.password)

    return client


@pytest.fixture
def admin_user(db):
    """ An admin user.
    """
    username = 'test_admin'
    password = 'password'

    user, created = User.objects.get_or_create(
        username=username, is_staff=True)

    if created:
        user.set_password(password)
        user.save()

    user.password = password

    return user


@pytest.fixture
def admin_user_client(db, admin_user):
    """A Django test client logged in as an admin user"""
    client = Client()
    client.login(username=admin_user.username, password=admin_user.password)

    return client



# Add mock acquisitions for tests
mock_acquire = actions.acquire_single_freq_fft.SingleFrequencyFftAcquisition(
    frequency=1e9,    # 1 GHz
    sample_rate=1e6,  # 1 MSa/s
    fft_size=16,
    nffts=11
)
mock_acquire.usrp = actions.tests.mocks.usrp

actions.by_name['mock_acquire'] = mock_acquire
actions.init()
