import collections
import time
from itertools import chain, count, islice


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
        next(islice(iterator, n, n), None)


# https://docs.python.org/3/library/itertools.html#itertools-recipes
def flatten(list_of_lists):
    "Flatten one level of nesting"
    return chain.from_iterable(list_of_lists)
