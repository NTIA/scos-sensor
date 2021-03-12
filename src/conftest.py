import pytest
from django.conf import settings
from django.test.client import Client

import actions
import scheduler
import shutil
from authentication.models import User
from tasks.models import TaskResult

@pytest.fixture(autouse=True)
def cleanup_db(db):
    yield
    # cleans up acquisition data files
    TaskResult.objects.all().delete()
    shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)


@pytest.yield_fixture
def testclock():
    """Replace scheduler's timefn with manually steppable test timefn."""
    # Setup test clock
    real_timefn = scheduler.utils.timefn
    real_delayfun = scheduler.utils.delayfn
    scheduler.utils.timefn = scheduler.tests.utils.TestClock()
    scheduler.utils.delayfn = scheduler.tests.utils.delayfn
    yield
    # Teardown test clock
    scheduler.utils.timefn = real_timefn
    scheduler.utils.delayfn = real_delayfun


@pytest.fixture
def test_scheduler(rf, testclock):
    """Instantiate test scheduler with fake request context and testclock."""
    s = scheduler.scheduler.Scheduler()
    s.request = rf.post("mock://cburl/schedule")
    return s


@pytest.fixture
def user(db):
    """A normal user."""
    username = "test"
    password = "password"

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
    username = "alt_test"
    password = "password"

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
    client.login(username=alt_user.username, password=alt_user.password)

    return client


@pytest.fixture
def alt_admin_user(db, django_user_model, django_username_field):
    """A Django admin user.

    This uses an existing user with username "alt_admin", or creates a new one
    with password "password".

    """
    UserModel = django_user_model
    username_field = django_username_field

    try:
        user = UserModel._default_manager.get(**{username_field: "alt_admin"})
    except UserModel.DoesNotExist:
        extra_fields = {}

        if username_field != "username":
            extra_fields[username_field] = "alt_admin"

        user = UserModel._default_manager.create_superuser(
            "alt_admin", "alt_admin@example.com", "password", **extra_fields
        )

    return user


@pytest.fixture
def alt_admin_client(db, alt_admin_user):
    """A Django test client logged in as an admin user."""
    from django.test.client import Client

    client = Client()
    client.login(username=alt_admin_user.username, password="password")

    return client


# Add mock acquisitions for tests
mock_acquire_single_frequency_fft = actions.acquire_single_freq_fft.SingleFrequencyFftAcquisition(
    name="mock_acquire_single_frequency_fft",
    frequency=1e9,  # 1 GHz
    gain=40,
    sample_rate=1e6,  # 1 MSa/s
    fft_size=16,
    nffts=11,
)
actions.by_name["mock_acquire_single_frequency_fft"] = mock_acquire_single_frequency_fft

# Add mock multi-recording acquisition for tests
stepped_freq_action = actions.acquire_stepped_freq_tdomain_iq
mock_multirec_acquire = stepped_freq_action.SteppedFrequencyTimeDomainIqAcquisition(
    name="mock_multirec_acquire",
    fcs=[1.1e9, 1.2e9, 1.3e9],  # 1400, 1500, 1600 MHz
    gains=[40, 40, 60],
    sample_rates=[1e6, 1e6, 1e6],  # 1 MSa/s
    durations_ms=[1, 2, 1],
)
actions.by_name["mock_multirec_acquire"] = mock_multirec_acquire

mock_time_domain_iq_acquire = stepped_freq_action.SteppedFrequencyTimeDomainIqAcquisition(
    name="mock_time_domain_iq_acquire",
    fcs=[1.1e9],  # 1400, 1500, 1600 MHz
    gains=[40],
    sample_rates=[1e6],  # 1 MSa/s
    durations_ms=[1],
)
actions.by_name["mock_time_domain_iq_acquire"] = mock_time_domain_iq_acquire

actions.init()
