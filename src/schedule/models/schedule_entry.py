import sys
from itertools import count

from django.core.validators import MinValueValidator
from django.db import models

import actions
from scheduler import utils


if sys.version_info.major == 2:
    range = xrange  # noqa


DEFAULT_PRIORITY = 10


def next_schedulable_timefn():
    return utils.timefn() + 1


class ScheduleEntry(models.Model):
    """Describes a series of scheduler tasks.

    A schedule entry is at minimum a human readable name and an associated
    action. Combining different values of `start`, `stop`, `interval`, and
    `priority` allows for flexible task scheduling. If no start time is given,
    the scheduler begins scheduling tasks immediately. If no stop time is
    given, the scheduler continues scheduling tasks until the schedule entry's
    :attr:`is_active` flag is unset. If no interval is given, the scheduler
    will schedule exactly one task and then unset :attr:`is_active`.
    `interval=None` can be used with either an immediate or future start time.
    If two tasks are scheduled to run at the same time, they will be run in
    order of `priority`. If two tasks are scheduled to run at the same time and
    have the same `priority`, execution order is undefined.

    """

    # Implementation notes:
    #
    # Large series of tasks are possible due to the "laziness" of the internal
    # `range`-based representation of task times:
    #
    #     >>> sys.getsizeof(range(1, 2))
    #     48
    #     >>> sys.getsizeof(range(1, 20000000000000))
    #     48
    #
    # `take_until` consumes times up to `t` from the internal range by moving
    # `next_task_time` forward in time and returning a `range` representing the
    # taken time slice. No other methods or properties actually consume times.
    #
    #     >>> entry = ScheduleEntry(name='test', start=5, stop=10, interval=1,
    #     ...                       action='logger')
    #     >>> list(entry.take_until(7))
    #     [5, 6]
    #     >>> list(entry.get_remaining_times())
    #     [7, 8, 9]
    #     >>> entry.take_until(9)
    #     range(7, 9)
    #     >>> list(_)
    #     [7, 8]
    #
    # When `stop` is `None`, the schedule entry replaces `range` with
    # `itertools.count`. A `count` provides an interface compatible with a
    # range iterator, but it's best not to do something like
    # `list(e.get_remaining_times())` from the example above on one.

    name = models.SlugField(
        primary_key=True,
        help_text="The unique identifier used in URLs and filenames"
    )
    action = models.CharField(
        choices=actions.CHOICES,
        max_length=actions.MAX_LENGTH,
        help_text="The name of the action to be scheduled"
    )
    priority = models.SmallIntegerField(
        default=DEFAULT_PRIORITY,
        help_text=(
            "Lower number is higher priority (default={})"
        ).format(DEFAULT_PRIORITY)
    )
    start = models.BigIntegerField(
        default=next_schedulable_timefn,
        blank=True,
        help_text="Absolute time (epoch) to start, or leave blank for 'now'"
    )
    stop = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Absolute time (epoch) to stop, or leave blank for 'never'"
    )
    interval = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=(MinValueValidator(1),),
        help_text="Seconds between tasks, or leave blank to run once"
    )
    is_active = models.BooleanField(
        default=True,
        editable=True,
        help_text=("Indicates whether the entry should be removed from the "
                   "scheduler without removing it from the system")
    )
    is_private = models.BooleanField(
        default=False,
        editable=True,
        help_text=("Indicates whether the entry, and resulting data, are only "
                   "visible to admin")
    )
    callback_url = models.URLField(
        blank=True,
        help_text=("If given, the scheduler will POST a `TaskResult` JSON "
                   "object to this URL after each task completes")
    )

    # read-only fields
    next_task_time = models.BigIntegerField(
        null=True,
        editable=False,
        help_text="The time the next task is to be executed"
    )
    next_task_id = models.IntegerField(
        default=1,
        editable=False,
        help_text="The id of the next task to be executed"
    )
    created = models.DateTimeField(
        auto_now_add=True,
        help_text="The date the entry was created"
    )
    modified = models.DateTimeField(
        auto_now=True,
        help_text="The date the entry was modified"
    )
    owner = models.ForeignKey(
        'authentication.User',
        editable=False,
        related_name='schedule_entries',
        on_delete=models.CASCADE,
        help_text="The name of the user who owns the entry"
    )

    request = models.ForeignKey(
        'schedule.Request',
        null=True,  # null allowable for unit testing only
        editable=False,
        on_delete=models.CASCADE,
        help_text="The request that created the entry"
    )

    class Meta:
        db_table = 'schedule'
        ordering = ('created',)

    def __init__(self, *args, **kwargs):
        stop_is_relative = kwargs.pop('stop_is_relative', False)

        super(ScheduleEntry, self).__init__(*args, **kwargs)

        if stop_is_relative:
            self.stop = self.start + self.stop

        if self.next_task_time is None:
            self.next_task_time = self.start

        # used by .save to detect whether to reset .next_task_time
        self.__start = self.start
        self.__interval = self.interval

    def save(self, *args, **kwargs):
        if self.start != self.__start or self.interval != self.__interval:
            self.next_task_time = max(self.start, next_schedulable_timefn())
            self.__start = self.start
            self.__interval = self.interval

        super(ScheduleEntry, self).save(*args, **kwargs)

    def take_pending(self):
        """Take the range of times up to and including now."""
        now = utils.timefn()
        return self.take_until(now + 1)

    def take_until(self, t=None):
        """Take the range of times before `t`.

        :param t: a :func:`timefn` timestamp

        """
        times = self.get_remaining_times(until=t)
        if times:
            if self.interval:
                self.next_task_time = times[-1] + self.interval
            else:
                # interval is None and time consumed
                self.is_active = False

        return times

    def has_remaining_times(self):
        """Return :obj:`True` if task times remain, else :obj:`False`."""
        return self.next_task_time in self.get_remaining_times()

    def get_remaining_times(self, until=None):
        """Get a potentially infinite iterator of remaining task times."""
        if not self.is_active:
            return range(0)

        next_time = self.next_task_time
        stop = self.stop
        if until is None and stop is None:
            if self.interval:
                return count(next_time, self.interval)         # infinite
            else:
                return iter(range(next_time, next_time + 1))   # one-shot

        stop = min(t for t in (until, stop) if t is not None)
        interval = self.interval or abs(stop - next_time)
        if interval:
            return range(next_time, stop, interval)
        else:
            return range(next_time, next_time + 1)

    def get_next_task_id(self):
        next_task_id = self.next_task_id
        self.next_task_id += 1
        return next_task_id

    def __str__(self):
        fmtstr = 'name={}, pri={}, start={}, stop={}, ival={}, action={}'
        return fmtstr.format(
            self.name,
            self.priority,
            self.start,
            self.stop,
            self.interval,
            self.action
        )
