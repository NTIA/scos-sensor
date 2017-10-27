import pytest

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
def test_user():
    user_name, password = 'test', ''

    user, created = User.objects.get_or_create(username=user_name)

    if created:
        user.set_password(password)
        user.save()

    user.password = password

    return user
