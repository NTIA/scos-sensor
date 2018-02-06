import pytest
from django.test.client import Client

import actions
import actions.tests.mocks.usrp
import scheduler
from authentication.models import User


def pytest_addoption(parser):
    parser.addoption('--update-api-docs', action='store_true',
                     default=False, help="Ensure API docs match code")


def pytest_collection_modifyitems(config, items):
    """Skips `test_api_docs_up_to_date` if CLI option not passed."""
    if config.getoption('--update-api-docs'):
        # --update-api-docs given on cli: do not skip api doc generation
        return
    skip_api_gen = pytest.mark.skip(reason="didn't pass --update-api-docs")
    for item in items:
        if 'update_api_docs' in item.keywords:
            item.add_marker(skip_api_gen)


@pytest.yield_fixture
def test_scheduler(rf):
    """Instantiate test scheduler with fake request context.

    Replace scheduler's timefn with manually steppable test timefn.

    """
    # Setup test clock
    real_timefn = scheduler.scheduler.utils.timefn
    real_delayfun = scheduler.utils.delayfn
    scheduler.utils.timefn = scheduler.tests.utils.TestClock()
    scheduler.utils.delayfn = scheduler.tests.utils.delayfn

    s = scheduler.scheduler.Scheduler()
    s.request = rf.post('mock://cburl/schedule')
    yield s

    # Teardown test clock
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
def alt_user(db):
    """A normal user."""
    username = 'alt_test'
    password = 'password'

    user, created = User.objects.get_or_create(username=username)

    if created:
        user.set_password(password)
        user.save()

    user.password = password

    return user


@pytest.fixture
def alt_user_client(db, alt_user):
    """A Django test client logged in as a normal user"""
    client = Client()
    client.login(
        username=alt_user.username, password=alt_user.password)

    return client


@pytest.fixture
def alt_admin_user(db, django_user_model, django_username_field):
    """A Django admin user.

    This uses an existing user with username "admin", or creates a new one with
    password "password".

    """
    UserModel = django_user_model
    username_field = django_username_field

    try:
        user = UserModel._default_manager.get(
            **{username_field: 'alt_admin'})
    except UserModel.DoesNotExist:
        extra_fields = {}

        if username_field != 'username':
            extra_fields[username_field] = 'alt_admin'

        user = UserModel._default_manager.create_superuser(
            'alt_admin', 'alt_admin@example.com', 'password',
            **extra_fields)

    return user


@pytest.fixture
def alt_admin_client(db, alt_admin_user):
    """A Django test client logged in as an admin user."""
    from django.test.client import Client

    client = Client()
    client.login(username=alt_admin_user.username, password='password')

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
