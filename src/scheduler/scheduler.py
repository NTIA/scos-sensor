"""Queue and run tasks."""

import json
import logging
import threading
from contextlib import contextmanager
from pathlib import Path

import requests
from django.conf import settings
from django.utils import timezone
from scos_actions.hardware.sensor import Sensor
from scos_actions.signals import trigger_api_restart

from initialization import action_loader, sensor_loader
from schedule.models import ScheduleEntry
from tasks.consts import MAX_DETAIL_LEN
from tasks.models import TaskResult
from tasks.serializers import TaskResultSerializer
from tasks.task_queue import TaskQueue

from . import utils

logger = logging.getLogger(__name__)


class Scheduler(threading.Thread):
    """A memory-friendly task scheduler."""

    def __init__(self):
        threading.Thread.__init__(self)
        self.task_status_lock = threading.Lock()
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
        self.last_status = ""
        self.consecutive_failures = 0
        self._sensor = sensor_loader.sensor

    @property
    def sensor(self):
        return self._sensor

    @sensor.setter
    def sensor(self, sensor: Sensor):
        logger.debug(f"Set scheduler sensor to {sensor}")
        self._sensor = sensor

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
            self.calibrate_if_needed()
            self.reset_next_task_id()
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
            task_result = self._initialize_task_result()
            started = timezone.now()
            status, detail = self._call_task_action()
            finished = timezone.now()
            if settings.ASYNC_CALLBACK:
                finalize_task_thread = threading.Thread(
                    target=self._finalize_task_result,
                    args=(task_result, started, finished, status, detail),
                    daemon=True,
                )
                finalize_task_thread.start()
            else:
                self._finalize_task_result(
                    task_result, started, finished, status, detail
                )

    def _initialize_task_result(self) -> TaskResult:
        """Initalize an 'in-progress' result so it exists when action runs."""
        tid = self.task.task_id
        task_result = TaskResult(schedule_entry=self.entry, task_id=tid)
        logger.debug(f"Creating task result with task id = {tid}")
        task_result.save()
        if tid > 1:
            last_task_id_exists = TaskResult.objects.filter(task_id=tid-1).exists()
            if not last_task_id_exists:
                logger.debug(f"TaskResult for tid = {tid-1} does not exist. Stopping schedule.")
                self.entry.is_active = False
                self.entry.save()
                raise Exception(f"Task ID Mismatch! last task id = {tid-1} current task id = {tid}")
        return task_result

    def _call_task_action(self):
        entry_name = self.task.schedule_entry_name
        task_id = self.task.task_id
        from schedule.serializers import ScheduleEntrySerializer

        schedule_entry = ScheduleEntry.objects.get(name=entry_name)

        schedule_serializer = ScheduleEntrySerializer(
            schedule_entry, context={"request": schedule_entry.request}
        )
        schedule_entry_json = schedule_serializer.to_sigmf_json()
        schedule_entry_json["id"] = entry_name

        try:
            logger.debug(
                f"running task {entry_name}/{task_id} with sigan: {self.sensor.signal_analyzer}"
            )
            detail = self.task.action_caller(self.sensor, schedule_entry_json, task_id)
            self.delayfn(0)  # let other threads run
            status = "success"
            if not isinstance(detail, str):
                detail = ""
        except Exception as err:
            detail = str(err)
            logger.exception(f"action failed: {detail}")
            status = "failure"

        return status, detail[:MAX_DETAIL_LEN]

    def _finalize_task_result(self, task_result, started, finished, status, detail):
        task_result.started = started
        task_result.finished = finished
        task_result.duration = finished - started
        task_result.status = status
        task_result.detail = detail
        task_result.save()

        if self.entry.callback_url:
            try:
                logger.debug("Trying callback to URL: " + self.entry.callback_url)
                context = {"request": self.entry.request}
                result_json = TaskResultSerializer(task_result, context=context).data
                verify_ssl = settings.CALLBACK_SSL_VERIFICATION
                if settings.CALLBACK_SSL_VERIFICATION:
                    if settings.PATH_TO_VERIFY_CERT != "":
                        verify_ssl = settings.PATH_TO_VERIFY_CERT
                logger.debug(settings.CALLBACK_AUTHENTICATION)
                if settings.CALLBACK_AUTHENTICATION == "CERT":
                    headers = {"Content-Type": "application/json"}

                    response = requests.post(
                        self.entry.callback_url,
                        data=json.dumps(result_json),
                        headers=headers,
                        verify=verify_ssl,
                        cert=settings.PATH_TO_CLIENT_CERT,
                        timeout=settings.CALLBACK_TIMEOUT,
                    )
                    self._callback_response_handler(response, task_result)
                else:
                    logger.debug("Posting callback with token")
                    token = self.entry.owner.auth_token
                    headers = {"Authorization": "Token " + str(token)}
                    response = requests.post(
                        self.entry.callback_url,
                        json=result_json,
                        headers=headers,
                        verify=verify_ssl,
                        timeout=settings.CALLBACK_TIMEOUT,
                    )
                    logger.debug("posted callback")
                    self._callback_response_handler(response, task_result)
            except Exception as err:
                logger.error(str(err))
                task_result.status = "notification_failed"
                task_result.save()
        else:
            task_result.save()

        with self.task_status_lock:
            self.last_status = status
            if status == "failure" and self.last_status == "failure":
                self.consecutive_failures = self.consecutive_failures + 1
            elif status == "failure":
                self.consecutive_failures = 1
            else:
                self.consecutive_failures = 0
            if self.consecutive_failures >= settings.MAX_FAILURES:
                trigger_api_restart.send(sender=self.__class__)
                # prevent more tasks from being run
                # restart can cause missing db task result ids
                # if tasks continue to run waiting for restart
                thread.stop()

    @staticmethod
    def _callback_response_handler(resp, task_result):
        if resp.ok:
            logger.debug(f"POSTed to {resp.url}")
        else:
            msg = "Failed to POST to {}: {}"
            logger.warning(msg.format(resp.url, resp.reason))
            task_result.status = "notification_failed"

        task_result.save()

    def _queue_pending_tasks(self, schedule_snapshot):
        pending_queue = TaskQueue()
        for entry in schedule_snapshot:
            task_time = self._take_pending_task_time(entry)
            self._cancel_if_completed(entry)
            if task_time is None:
                continue

            # count = TaskResult.objects.filter(schedule_entry=entry).count()
            # if count > 0:
            #     last_task_id = TaskResult.objects.filter(schedule_entry=entry).order_by("task_id")[count-1].task_id
            #     entry.next_task_id = last_task_id + 1
            # current_task_id = entry.next_task_id
            # if  TaskResult.objects.filter(schedule_entry=entry, task_id=current_task_id).count() == 0:
            #     task_id = current_task_id
            #     logger.debug(f"Not task result exists for {current_task_id} using {task_id} for next task id.")
            # else:
            task_id = entry.get_next_task_id()
            logger.debug(f"Updating schedule entry next task id, task_id = {task_id}")
            entry.save(update_fields=("next_task_id",))
            logger.debug(f"entry.next_task_id = {entry.next_task_id}")
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
            msg = f"no times remaining in {entry.name}, removing"
            logger.info(msg)
            self.cancel(entry)

    @property
    def status(self):
        if self.is_alive():
            return "running" if self.running else "idle"
        return "dead"

    def __repr__(self):
        s = "running" if self.running else "stopped"
        return f"<{self.__class__.__name__} status={s}>"

    def calibrate_if_needed(self):
        # Now run the calibration action defined in the environment
        # This will create an onboard_cal file if needed, and set it
        # as the sensor's sensor_calibration.
        if settings.MOCK_SIGAN:
            logger.debug("Skipping startup calibration when using mock sigan")
            return
        if not settings.RUNNING_MIGRATIONS:
            if (
                sensor_loader.sensor.sensor_calibration is None
                or sensor_loader.sensor.sensor_calibration.expired()
            ):
                if settings.STARTUP_CALIBRATION_ACTION is None:
                    logger.error("No STARTUP_CALIBRATION_ACTION set.")
                else:
                    logger.info("Performing startup calibration...")
                    try:
                        cal_action = action_loader.actions[
                            settings.STARTUP_CALIBRATION_ACTION
                        ]
                        cal_action(
                            sensor=sensor_loader.sensor,
                            schedule_entry=None,
                            task_id=None,
                        )
                    except BaseException as cal_error:
                        logger.error(f"Error during startup calibration: {cal_error}")
            else:
                logger.debug(
                    "Skipping startup calibration since sensor_calibration exists and has not expired."
                )

    def reset_next_task_id(self):
        # reset next task id
        for entry in self.schedule:
            count = TaskResult.objects.filter(schedule_entry=entry).count()
            if count > 0:
                last_task_id = TaskResult.objects.filter(schedule_entry=entry).order_by("task_id")[count-1].task_id
                entry.next_task_id = last_task_id + 1
                entry.save(update_fields=("next_task_id",))


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
