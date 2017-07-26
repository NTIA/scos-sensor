"""Schedule and run tasks.

Example usage:
    >>> from scheduler import Scheduler, ScheduleEntry
    >>> e1 = ScheduleEntry(name='oneshot', priority=10, action='logger')
    >>> e2 = ScheduleEntry(name='fivetimes', priority=20, action='logger',
    ...                    interval=1, relative_stop=True)
    >>> # 'oneshot' has no interval and higher priority, so it will go first
    ... # and then 'fivetimes' will get called five times and then exit
    ... s = Scheduler()
    >>> s.schedule.add(e1)
    >>> s.schedule.add(e2)
    >>> s.run()
    [...] INFO in actions: oneshot
    [...] INFO in actions: fivetimes
    [...] INFO in actions: fivetimes
    [...] INFO in actions: fivetimes
    [...] INFO in actions: fivetimes
    [...] INFO in actions: fivetimes
    [...] INFO in scheduler: all scheduled tasks completed
"""

import atexit
import logging
import threading

from . import utils
from .models import ScheduleEntry
from .tasks import TaskQueue


logger = logging.getLogger(__name__)


class Scheduler(threading.Thread):
    """A memory-friendly task scheduler."""
    def __init__(self):
        threading.Thread.__init__(self)
        self.timefn = utils.timefn
        self.delayfn = utils.delayfn

        self.task_queue = TaskQueue()

        # scheduler looks ahead `interval_multiplier` times the shortest
        # interval in the schedule in order to keep memory-usage low
        self.interval_multiplier = 10
        self.name = "Scheduler"
        self.running = False
        self.interrupt_flag = threading.Event()

        self.app = None

    @property
    def schedule(self):
        """An updated view of the current schedule"""
        return ScheduleEntry.objects.filter(canceled=False).all()

    def stop(self):
        """Complete the current task, then return control."""
        self.interrupt_flag.set()

    def start(self):
        """Run the scheduler in its own thread and return control."""
        threading.Thread.start(self)

    @staticmethod
    def cancel(entry):
        entry.canceled = True
        entry.save()

    def run(self, blocking: bool = True):
        """Run the scheduler in the current thread.

        :param blocking: block until stopped or return control after each task

        """
        while True:
            self._consume_schedule(blocking)

            if not blocking or self.interrupt_flag.is_set():
                break

            self.delayfn(0.25)

    def _consume_schedule(self, blocking):
        while self.schedule:
            self.running = True

            schedule_snapshot = self.schedule
            pending_task_queue = self._queue_tasks(schedule_snapshot)
            self._call_task_actions(pending_task_queue)

            if not blocking or self.interrupt_flag.is_set():
                break

            self.delayfn(0.25)
        else:
            self.task_queue.clear()
            if self.running:
                logger.info("all scheduled tasks completed")

        self.running = False

    def _queue_tasks(self, schedule_snapshot):
        pending_task_queue = self._queue_pending_tasks(schedule_snapshot)
        self.task_queue = self._queue_upcoming_tasks(schedule_snapshot)

        return pending_task_queue

    def _call_task_actions(self, pending_task_queue):
        for next_task in pending_task_queue.to_list():
            entry_name = next_task.schedule_entry_name
            task_id = next_task.task_id
            try:
                logger.debug("running task {}/{}".format(entry_name, task_id))
                next_task.action_fn(entry_name, task_id)
                self.delayfn(0)  # let other threads run
            except:
                logger.exception("action failed")

    def _queue_pending_tasks(self, schedule_snapshot):
        pending_queue = TaskQueue()
        for entry in schedule_snapshot:
            task_time = self._take_pending_task_time(entry)
            self._cancel_if_completed(entry)
            if task_time is None:
                continue

            task_id = entry.get_next_task_id()
            entry.save()
            pri = entry.priority
            action = entry.action
            pending_queue.enter(task_time, pri, action, entry.name, task_id)

        return pending_queue

    def _take_pending_task_time(self, entry):
        task_times = entry.take_pending()
        entry.save()
        if not task_times:
            return None

        most_recent = self._compress_past_task_times(task_times, entry.name)
        return most_recent

    @staticmethod
    def _compress_past_task_times(past, schedule_entry_name):
        npast = len(past)
        if npast > 1:
            msg = "skipping {} {} tasks with times in the past"
            logger.warning(msg.format(npast - 1, schedule_entry_name))

        most_recent = past[-1]
        return most_recent

    def _queue_upcoming_tasks(self, schedule_snapshot):
        upcoming_queue = TaskQueue()
        upcoming_task_times = self._get_upcoming_task_times(schedule_snapshot)
        for entry, task_times in upcoming_task_times.items():
            task_id = None
            pri = entry.priority
            action = entry.action
            for t in task_times:
                upcoming_queue.enter(t, pri, action, entry.name, task_id)

        return upcoming_queue

    def _get_upcoming_task_times(self, schedule_snapshot):
        upcoming_task_times = {}
        now = self.timefn()
        min_interval = self._get_min_interval(schedule_snapshot)
        lookahead = now + min_interval * self.interval_multiplier
        for entry in schedule_snapshot:
            task_times = entry.get_remaining_times(until=lookahead)
            upcoming_task_times[entry] = task_times

        return upcoming_task_times

    def _get_min_interval(self, schedule_snapshot):
        intervals = (e.interval for e in schedule_snapshot if e.interval)
        return min(intervals, default=1)

    def _cancel_if_completed(self, entry):
        if not entry.has_remaining_times():
            msg = "no times remaining in {}, removing".format(entry.name)
            logger.debug(msg)
            self.cancel(entry)

    def __repr__(self):
        s = "running" if self.running else "stopped"
        return "<{} status={}>".format(self.__class__.__name__, s)


# The (small) price we pay for putting the scheduler thread right here instead
# of running it in its own microservice is that we _must not_ run the
# application server in multiple processes (multiple threads are fine).
thread = Scheduler()


def stop_scheduler(*args):
    if thread.is_alive():
        logger.info("Stopping scheduler")
        thread.stop()


atexit.register(stop_scheduler)
