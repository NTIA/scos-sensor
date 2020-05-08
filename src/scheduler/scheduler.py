"""Queue and run tasks."""

import logging
import threading
from contextlib import contextmanager
from pathlib import Path

from django.utils import timezone
from requests_futures.sessions import FuturesSession

from schedule.models import ScheduleEntry
from sensor import settings
from tasks.consts import MAX_DETAIL_LEN
from tasks.models import TaskResult
from tasks.serializers import TaskResultSerializer
from tasks.task_queue import TaskQueue

from . import utils
from capabilities import capabilities

logger = logging.getLogger(__name__)
requests_futures_session = FuturesSession()


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

        # Cache the currently running task state
        self.entry = None  # ScheduleEntry that created the current task
        self.task = None  # Task object describing current task
        self.task_result = None  # TaskResult object for current task

    @property
    def schedule(self):
        """An updated view of the current schedule"""
        return ScheduleEntry.objects.filter(is_active=True).all()

    @property
    def schedule_has_entries(self):
        """True if active events exist in the schedule, otherwise False."""
        return ScheduleEntry.objects.filter(is_active=True).exists()

    @staticmethod
    def cancel(entry):
        """Remove an entry from the scheduler without deleting it."""
        entry.is_active = False
        entry.save(update_fields=("is_active",))

    def stop(self):
        """Complete the current task, then return control."""
        self.interrupt_flag.set()

    def start(self):
        """Run the scheduler in its own thread and return control."""
        threading.Thread.start(self)

    def run(self, blocking=True):
        """Run the scheduler in the current thread.

        :param blocking: block until stopped or return control after each task

        """
        if blocking:
            try:
                Path(settings.SCHEDULER_HEALTHCHECK_FILE).unlink()
            except FileNotFoundError:
                pass

        try:
            while True:
                with minimum_duration(blocking):
                    self._consume_schedule(blocking)

                if not blocking or self.interrupt_flag.is_set():
                    logger.info("scheduler interrupted")
                    break
        except Exception as err:
            logger.warning("scheduler dead")
            logger.exception(err)
            if settings.IN_DOCKER:
                Path(settings.SCHEDULER_HEALTHCHECK_FILE).touch()

    def _consume_schedule(self, blocking):
        while self.schedule_has_entries:
            with minimum_duration(blocking):
                self.running = True
                schedule_snapshot = self.schedule
                pending_task_queue = self._queue_tasks(schedule_snapshot)
                self._consume_task_queue(pending_task_queue)

            if not blocking or self.interrupt_flag.is_set():
                break
        else:
            self.task_queue.clear()
            if self.running:
                logger.info("all scheduled tasks completed")

        self.running = False

    def _queue_tasks(self, schedule_snapshot):
        pending_task_queue = self._queue_pending_tasks(schedule_snapshot)
        self.task_queue = self._queue_upcoming_tasks(schedule_snapshot)

        return pending_task_queue

    def _consume_task_queue(self, pending_task_queue):
        for task in pending_task_queue.to_list():
            entry_name = task.schedule_entry_name
            self.task = task
            self.entry = ScheduleEntry.objects.get(name=entry_name)
            self._initialize_task_result()
            started = timezone.now()
            status, detail = self._call_task_action()
            finished = timezone.now()
            self._finalize_task_result(started, finished, status, detail)

    def _initialize_task_result(self):
        """Initalize an 'in-progress' result so it exists when action runs."""
        tid = self.task.task_id
        self.task_result = TaskResult(schedule_entry=self.entry, task_id=tid)
        self.task_result.save()

    def _call_task_action(self):
        entry_name = self.task.schedule_entry_name
        task_id = self.task.task_id
        time = self.task.time
        from schedule.serializers import ScheduleEntrySerializer
        from tasks.serializers import TaskResultSerializer

        schedule_entry = ScheduleEntry.objects.get(name=entry_name)

        schedule_serializer = ScheduleEntrySerializer(
            schedule_entry, context={"request": schedule_entry.request}
        )
        schedule_entry_json = schedule_serializer.to_sigmf_json()
        schedule_entry_json["id"] = entry_name

        try:
            logger.debug("running task {}/{}".format(entry_name, task_id))
            if self.entry.GPS_sync_start:
                ## time was delayed 5 seconds when GPS_sync_start is True (in schedule_entry.__init__() method)
                ## adding those 5 seconds back now.
                schedule_entry_json['GPS_sync_start'] = time + 5
            detail = self.task.action_caller(
                schedule_entry_json, task_id, capabilities["sensor"]
            )
            self.delayfn(0)  # let other threads run
            status = "success"
            if not isinstance(detail, str):
                detail = ""
        except Exception as err:
            detail = str(err)
            logger.exception("action failed: {}".format(detail))
            status = "failure"

        return status, detail[:MAX_DETAIL_LEN]

    def _finalize_task_result(self, started, finished, status, detail):
        tr = self.task_result
        tr.started = started
        tr.finished = finished
        tr.duration = finished - started
        tr.status = status
        tr.detail = detail
        tr.save()

        if self.entry.callback_url:
            try:
                logger.debug("Trying callback to URL: " + self.entry.callback_url)
                context = {"request": self.entry.request}
                result_json = TaskResultSerializer(tr, context=context).data
                token = self.entry.owner.auth_token
                headers = {"Authorization": "Token " + str(token)}
                verify_ssl = settings.CALLBACK_SSL_VERIFICATION
                requests_futures_session.post(
                    self.entry.callback_url,
                    json=result_json,
                    background_callback=self._callback_response_handler,
                    headers=headers,
                    verify=verify_ssl,
                )
            except Exception as err:
                logger.error(str(err))

    @staticmethod
    def _callback_response_handler(sess, resp):
        if resp.ok:
            logger.info("POSTed to {}".format(resp.url))
        else:
            msg = "Failed to POST to {}: {}"
            logger.warning(msg.format(resp.url, resp.reason))

    def _queue_pending_tasks(self, schedule_snapshot):
        pending_queue = TaskQueue()
        for entry in schedule_snapshot:
            task_time = self._take_pending_task_time(entry)
            self._cancel_if_completed(entry)
            if task_time is None:
                continue

            task_id = entry.get_next_task_id()
            entry.save(update_fields=("next_task_id",))
            pri = entry.priority
            action = entry.action
            pending_queue.enter(task_time, pri, action, entry.name, task_id)

        return pending_queue

    def _take_pending_task_time(self, entry):
        task_times = entry.take_pending()
        entry.save(update_fields=("next_task_time", "is_active"))
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
        intervals = [e.interval for e in schedule_snapshot if e.interval]
        return min(intervals, default=1)

    def _cancel_if_completed(self, entry):
        if not entry.has_remaining_times():
            msg = "no times remaining in {}, removing".format(entry.name)
            logger.debug(msg)
            self.cancel(entry)

    @property
    def status(self):
        if self.is_alive():
            return "running" if self.running else "idle"
        return "dead"

    def __repr__(self):
        s = "running" if self.running else "stopped"
        return "<{} status={}>".format(self.__class__.__name__, s)


@contextmanager
def minimum_duration(blocking):
    """Ensure a code block is entered at most once per timefn rollover.

    :param blocking: if False, minimum duration is 0

    """
    start_time = utils.timefn()
    yield
    while blocking and utils.timefn() == start_time:
        utils.delayfn(0.01)


# The (small) price we pay for putting the scheduler thread right here instead
# of running it in its own microservice is that we _must not_ run the
# application server in multiple processes (multiple threads are fine).
thread = Scheduler()
