import collections
import logging
import threading
import time
from itertools import chain, count, islice

from authentication.models import User
from schedule.models import Request, ScheduleEntry
from scheduler.scheduler import Scheduler
from sensor import V1
from django.conf import settings
from scos_actions.hardware.mocks.mock_sigan import MockSignalAnalyzer

actions = settings.actions
BAD_ACTION_STR = "testing expected failure"

logger = logging.getLogger(__name__)
logger.debug("*************** scos-sensor/scheduler/test/utils ***********")


class TestClock:
    """Manually-incremented clock counter"""

    def __init__(self):
        self.clock = count()
        self.t = next(self.clock)

    def __iter__(self):
        return self

    def __next__(self):
        self.t = next(self.clock)
        return self.t

    def __call__(self):
        return self.t


TestClock.next = TestClock.__next__  # py2.7 compat


def delayfn(t):
    """Delay fn that doesn't delay"""
    time.sleep(0)


# https://docs.python.org/3/library/itertools.html#itertools-recipes
def advance_testclock(iterator, n):
    "Advance the iterator n-steps ahead. If n is None, consume entirely."
    # Use functions that consume iterators at C speed.
    if n is None:
        # feed the entire iterator into a zero-length deque
        collections.deque(iterator, maxlen=0)
    else:
        # advance to the empty slice starting at position n
        try:
            next(islice(iterator, n, n), None)
        except TypeError:
            err = "This test case requires the 'test_scheduler' fixture."
            raise TypeError(err)


def simulate_scheduler_run(n=1):
    s = Scheduler()
    s.signal_analyzer = MockSignalAnalyzer()
    for _ in range(n):
        advance_testclock(s.timefn, 1)
        s.run(blocking=False)


def create_entry(name, priority, start, stop, interval, action, cb_url=None):
    kwargs = {
        "name": name,
        "priority": priority,
        "stop": stop,
        "interval": interval,
        "action": action,
        "owner": User.objects.get_or_create(username="test")[0],
    }

    if start is not None:
        kwargs["start"] = start

    if cb_url is not None:
        kwargs["callback_url"] = cb_url

    r = Request()
    r.scheme = "https"
    r.version = V1["version"]
    r.host = "testserver"
    r.save()
    schedule_entry = ScheduleEntry(**kwargs)
    schedule_entry.request = r
    schedule_entry.save()

    return schedule_entry


def create_action():
    """Register an action that sets a thread-safe event flag when run.

    For each call, a separate named action is created using static `counter`
    variable.

    See `test_calls_actions` for usage example.

    """
    flag = threading.Event()

    def cb(schedule_entry_json, task_id):
        flag.set()
        return "set flag"

    cb.__name__ = "testcb" + str(create_action.counter)
    actions[cb.__name__] = cb
    create_action.counter += 1

    return cb, flag


create_action.counter = 0


def create_bad_action():
    def bad_action(sigan, gps, schedule_entry_json, task_id):
        raise Exception(BAD_ACTION_STR)

    actions["bad_action"] = bad_action
    return bad_action


# https://docs.python.org/3/library/itertools.html#itertools-recipes
def flatten(list_of_lists):
    "Flatten one level of nesting"
    return chain.from_iterable(list_of_lists)
