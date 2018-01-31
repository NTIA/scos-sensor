import collections
import time
from itertools import chain, count, islice

from scheduler.scheduler import Scheduler


class TestClock(object):
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


def fast_timefn():
    """10 Hz clock"""
    return int(time.time()*10)


def fast_delayfn(d):
    return time.sleep(d/10)


# https://docs.python.org/3/library/itertools.html#itertools-recipes
def advance_testclock(iterator, n):
    "Advance the iterator n-steps ahead. If n is none, consume entirely."
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
    for _ in range(n):
        advance_testclock(s.timefn, 1)
        s.run(blocking=False)


# https://docs.python.org/3/library/itertools.html#itertools-recipes
def flatten(list_of_lists):
    "Flatten one level of nesting"
    return chain.from_iterable(list_of_lists)
