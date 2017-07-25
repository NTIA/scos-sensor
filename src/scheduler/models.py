from itertools import count
from typing import Iterable

from django.db import models

import actions
from . import utils


DEFAULT_PRIORITY = 10


class ScheduleEntry(models.Model):
    name = models.SlugField(primary_key=True)
    action = models.CharField(choices=actions.CHOICES,
                              max_length=actions.MAX_LENGTH)
    priority = models.SmallIntegerField(default=DEFAULT_PRIORITY)
    start = models.BigIntegerField(default=utils.timefn, blank=True)
    stop = models.BigIntegerField(null=True, blank=True)
    relative_stop = models.BooleanField(default=False)
    interval = models.IntegerField(null=True, blank=True)
    canceled = models.BooleanField(default=False, editable=False)
    next_task_id = models.IntegerField(default=1, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "schedule"
        ordering = ("created_at",)

    def take_pending(self):
        """Take the range of times up to and including now."""
        now = utils.timefn()
        return self.take_until(now+1)

    def take_until(self, t: int = None) -> range:
        """Take the range of times before `t`.

        :param t: a :func:`utils.timefn`

        """
        times = self.get_remaining_times(until=t)
        if times:
            if self.interval:
                next_t = times[-1] + self.interval
                self.start = next_t
            else:
                # interval is None and time consumed
                self.canceled = True

        return times

    def has_remaining_times(self) -> bool:
        """Return :obj:`True` if task times remain, else :obj:`False`."""
        return self.start in self.get_remaining_times()

    def get_remaining_times(self, until: int = None) -> Iterable[int]:
        """Get a potentially infinite iterator of remaining task times."""
        if self.canceled:
            return range(0)

        stop = self.stop

        if until is None and stop is None:
            if self.interval:
                return count(self.start, self.interval)         # infinite
            else:
                return iter(range(self.start, self.start + 1))  # one-shot

        if self.relative_stop and stop:
            stop = self.start + stop

        stop = min(t for t in (until, stop) if t is not None)

        interval = self.interval or abs(stop - self.start)
        times = range(self.start, stop, interval)
        return times

    def get_next_task_id(self):
        next_task_id = self.next_task_id
        self.next_task_id += 1
        return next_task_id
