import time
import threading

import pytest
import requests_mock

from scheduler.scheduler import Scheduler, minimum_duration
from .utils import (BAD_ACTION_STR, advance_testclock, create_action,
                    create_bad_action, create_entry)


@pytest.mark.django_db
def test_populate_queue(test_scheduler):
    """An entry in the schedule should be added to a read-only task queue."""
    create_entry('test', 1, 0, 5, 1, 'logger')
    s = test_scheduler
    s.run(blocking=False)  # now=0, so task with time 0 is run
    assert [e.time for e in s.task_queue] == [1, 2, 3, 4]


@pytest.mark.django_db
def test_priority(test_scheduler):
    """A task with lower priority number should sort higher in task queue."""
    lopri = 20
    hipri = 10
    create_entry('lopri', lopri, 0, 5, 1, 'logger')
    create_entry('hipri', hipri, 0, 5, 1, 'logger')
    s = test_scheduler
    s.run(blocking=False)
    q = s.task_queue.to_list()
    assert len(test_scheduler.task_queue) == 8
    assert all(e.priority is hipri for e in q[::2])  # tasks at 0, 2...
    assert all(e.priority is lopri for e in q[1::2])  # tasks at 1, 3...


@pytest.mark.django_db
def test_future_start(test_scheduler):
    """An entry with start time in future should remain in schedule."""
    create_entry('t', 1, 50, 100, 1, 'logger')
    test_scheduler.run(blocking=False)
    s = test_scheduler
    assert len(s.task_queue) == 0
    assert len(s.schedule) == 1


@pytest.mark.django_db
def test_calls_actions(test_scheduler):
    """The scheduler should call task's action function at the right time."""
    # This test works by registering a few test actions and ensuring the
    # scheduler calls them.
    test_actions = dict(create_action() for _ in range(3))

    for i, cb in enumerate(test_actions):
        create_entry('test' + str(i), 1, 0, 3, 1, cb.__name__)

    s = test_scheduler
    s.run(blocking=False)
    advance_testclock(s.timefn, 5)
    assert s.timefn() == 5
    s.run(blocking=False)
    flags = test_actions.values()
    assert all([flag.is_set() for flag in flags])
    assert not s.running


@pytest.mark.django_db
def test_add_entry(test_scheduler):
    """Creating a new entry instance adds it to the current schedule."""
    create_entry('t1', 10, 1, 100, 5, 'logger')
    s = test_scheduler
    s.run(blocking=False)
    advance_testclock(s.timefn, 49)
    create_entry('t2', 20, 50, 300, 5, 'logger')
    s.run(blocking=False)
    assert len(s.task_queue) == 20
    assert s.task_queue[0].priority == 20


@pytest.mark.django_db
def test_remove_entry_by_delete(test_scheduler):
    """An entry is removed from schedule if it's deleted."""
    e1 = create_entry('t1', 10, 1, 300, 5, 'logger')
    e2 = create_entry('t2', 20, 50, 300, 5, 'logger')
    s = test_scheduler
    s.run(blocking=False)
    advance_testclock(s.timefn, 10)
    e1.delete()
    s.run(blocking=False)
    assert len(s.schedule) == 1
    assert e2 in s.schedule


@pytest.mark.django_db
def test_remove_entry_by_cancel(test_scheduler):
    """scheduler.cancel removes an entry from schedule without deleting it."""
    e1 = create_entry('t1', 10, 1, 300, 5, 'logger')
    e2 = create_entry('t2', 20, 50, 300, 5, 'logger')
    s = test_scheduler
    s.run(blocking=False)
    advance_testclock(s.timefn, 10)
    s.cancel(e1)
    s.run(blocking=False)
    assert len(s.schedule) == 1
    assert e2 in s.schedule


@pytest.mark.django_db(transaction=True)
def test_start_stop(test_scheduler):
    """Calling stop on started scheduler thread should cause thread exit."""
    create_entry('t', 1, 1, 100, 5, 'logger')
    s = test_scheduler
    s.start()
    time.sleep(0.02)  # hit minimum_duration
    advance_testclock(s.timefn, 1)
    s.stop()
    advance_testclock(s.timefn, 1)
    s.join()
    assert not s.running


@pytest.mark.django_db(transaction=True)
def test_run_completes(test_scheduler):
    """The scheduler should return to idle state after schedule completes."""
    create_entry('t', 1, None, None, None, 'logger')
    s = test_scheduler
    s.start()
    time.sleep(0.1)  # hit minimum_duration
    advance_testclock(s.timefn, 1)
    time.sleep(0.1)
    assert not s.running
    s.stop()
    advance_testclock(s.timefn, 1)
    s.join()


@pytest.mark.django_db
def test_survives_failed_action(test_scheduler):
    """An action throwing an exception should be survivable."""
    cb1 = create_bad_action()
    create_entry('t1', 10, None, None, None, cb1.__name__)
    cb2, flag = create_action()
    # less priority to force run after bad_entry fails
    create_entry('t2', 20, None, None, None, cb2.__name__)
    s = test_scheduler
    advance_testclock(s.timefn, 1)
    assert not flag.is_set()
    s.run(blocking=False)
    assert flag.is_set()


@pytest.mark.django_db
def test_compress_past_times(test_scheduler):
    """Multiple task times in the past should be compressed to one."""
    create_entry('t', 1, -10, 5, 1, 'logger')
    s = test_scheduler
    s.run(blocking=False)
    # past times -10 through 0 are compressed and a single task is run,
    # then 1, 2, 3, and 4 are queued
    assert len(s.task_queue) == 4


@pytest.mark.django_db
def test_compress_past_times_offset(test_scheduler):
    """Multiple task times in the past should be compressed to one."""
    create_entry('t', 1, -2, 14, 4, 'logger')
    s = test_scheduler
    s.run(blocking=False)
    # past time -2 is run, then 2, 6, and 10 are queued
    # NOTE: time 14 isn't included because range is [-2, 14) interval 4
    assert len(s.task_queue) == 3


# XXX: refactor
@pytest.mark.django_db
def test_next_task_time_value_when_start_changes(test_scheduler):
    """When an entry's start value changes, update `next_task_time`."""
    entry = create_entry('t', 1, 1, 10, 1, 'logger')
    s = test_scheduler
    s.run(blocking=False)
    assert entry.next_task_time == 1
    assert [task.time for task in s.task_queue[:5]] == [1, 2, 3, 4, 5]
    # recall now == 0, so default_start_timefn() => 1
    # set start before default_start_timefn value
    entry.start = 0
    entry.save()
    s.run(blocking=False)
    # expect no change
    entry.refresh_from_db()
    assert entry.next_task_time == 1
    assert [task.time for task in s.task_queue[:5]] == [1, 2, 3, 4, 5]
    # set start same as default_start_timefn value
    entry.start = 1
    entry.save()
    s.run(blocking=False)
    # expect no change
    entry.refresh_from_db()
    assert entry.next_task_time == 1
    assert [task.time for task in s.task_queue[:5]] == [1, 2, 3, 4, 5]
    # set start same ahead of default_start_timefn value
    entry.start = 2
    entry.save()
    s.run(blocking=False)
    # expect next_task_time to be start
    entry.refresh_from_db()
    assert entry.next_task_time == 2
    assert [task.time for task in s.task_queue[:5]] == [2, 3, 4, 5, 6]


# XXX: refactor
@pytest.mark.django_db
def test_next_task_time_value_when_interval_changes(test_scheduler):
    """When an entry's interval value changes, update `next_task_time`."""
    entry = create_entry('t', 1, 1, 100, 1, 'logger')
    s = test_scheduler
    s.run(blocking=False)
    assert entry.next_task_time == 1
    assert [task.time for task in s.task_queue[:5]] == [1, 2, 3, 4, 5]
    # recall now == 0, so default_start_timefn() => 1
    entry.interval = 5
    entry.save()
    s.run(blocking=False)
    entry.refresh_from_db()
    assert entry.start == 1
    assert entry.next_task_time == 1
    assert [task.time for task in s.task_queue[:5]] == [1, 6, 11, 16, 21]
    advance_testclock(s.timefn, 2)
    # now == 2, so default_start_timefn() => 3
    assert entry.start == entry.next_task_time == 1
    entry.interval = 10
    entry.save()
    s.run(blocking=False)
    entry.refresh_from_db()
    assert entry.start == 1
    assert entry.next_task_time == 3
    assert [task.time for task in s.task_queue[:5]] == [3, 13, 23, 33, 43]


@pytest.mark.django_db
def test_one_shot(test_scheduler):
    """If no start or interval given, entry should be run once and removed."""
    create_entry('t', 1, None, None, None, 'logger')
    s = test_scheduler
    advance_testclock(s.timefn, 1)
    s.run(blocking=False)
    assert len(s.task_queue) == 0
    assert not s.schedule_has_entries


@pytest.mark.django_db
def test_task_queue(test_scheduler):
    """The scheduler should maintain a queue of upcoming tasks."""
    e = create_entry('t', 1, 1, 100, 5, 'logger')
    s = test_scheduler

    # upcoming tasks are queued
    s.run(blocking=False)  # queue first 10 tasks
    assert len(s.task_queue) == 10

    # task queue is purely informational, IOW, adding tasks to task queue
    # doesn't consume them from the entry
    advance_testclock(s.timefn, 10)
    s.run(blocking=False)  # consume 2 tasks and queue 2 more tasks
    assert len(s.task_queue) == 10
    e.refresh_from_db()
    assert len(e.get_remaining_times()) == 100 / 5 - 2

    # canceled tasks are removed from task queue
    s.cancel(e)
    s.run(blocking=False)
    assert len(s.task_queue) == 0
    assert len(s.schedule) == 0


@pytest.mark.django_db
def test_clearing_schedule_clears_task_queue(test_scheduler):
    """The scheduler should empty task_queue when schedule is deleted."""
    create_entry('t', 1, 1, 100, 5, 'logger')
    s = test_scheduler
    s.run(blocking=False)  # queue first 10 tasks
    assert len(s.task_queue) == 10
    s.schedule.delete()
    s.run(blocking=False)
    assert len(s.task_queue) == 0


def test_minimum_duration_blocking():
    """minimum_duration should block until start of next second."""
    start = int(time.time())
    blocking = True
    with minimum_duration(blocking):
        pass

    stop = int(time.time())
    assert start != stop


def test_minimum_duration_non_blocking():
    """blocking=False should make minimum_duration return immediately."""
    start = time.time()
    blocking = False
    with minimum_duration(blocking):
        pass

    stop = time.time()
    one_ms = 0.001
    assert (stop - start) <= one_ms


@pytest.mark.django_db
def test_failure_posted_to_callback_url(test_scheduler):
    """If an entry has callback_url defined, scheduler should POST to it."""
    cb_flag = threading.Event()

    def cb_request_handler(sess, resp):
        cb_flag.set()

    cb = create_bad_action()
    create_entry('t', 10, None, None, None, cb.__name__, 'mock://cburl')
    s = test_scheduler
    advance_testclock(s.timefn, 1)
    s._callback_response_handler = cb_request_handler

    assert not cb_flag.is_set()

    request_json = None
    with requests_mock.Mocker() as m:
        m.post('mock://cburl')  # register url for posting
        s.run(blocking=False)
        time.sleep(0.1)  # let requests thread run
        request_json = m.request_history[0].json()

    assert cb_flag.is_set()
    assert request_json['result'] == 'failure'
    assert request_json['task_id'] == 1
    assert request_json['url']
    assert request_json['detail'] == BAD_ACTION_STR
    assert request_json['started']
    assert request_json['finished']
    assert request_json['duration']


@pytest.mark.django_db
def test_success_posted_to_callback_url(test_scheduler):
    """If an entry has callback_url defined, scheduler should POST to it."""
    cb_flag = threading.Event()

    def cb_request_handler(sess, resp):
        cb_flag.set()

    cb, action_flag = create_action()
    # less priority to force run after bad_entry fails
    create_entry('t', 20, None, None, None, cb.__name__, 'mock://cburl')
    s = test_scheduler
    advance_testclock(s.timefn, 1)
    s._callback_response_handler = cb_request_handler

    assert not action_flag.is_set()

    request_json = None
    with requests_mock.Mocker() as m:
        m.post('mock://cburl')  # register mock url for posting
        s.run(blocking=False)
        time.sleep(0.1)  # let requests thread run
        request_json = m.request_history[0].json()

    assert cb_flag.is_set()
    assert action_flag.is_set()
    assert request_json['result'] == 'success'
    assert request_json['task_id'] == 1
    assert request_json['url']
    assert request_json['started']
    assert request_json['finished']
    assert request_json['duration']


@pytest.mark.django_db
def test_starvation(test_scheduler):
    """A recurring high-pri task should not 'starve' a low-pri task."""
    # higher-pri recurring task that takes 3 ticks to complete enters at t=0
    cb0, flag0 = create_action()
    create_entry('t0', 10, None, None, 3, cb0.__name__)
    # lower-pri task enters at t=2
    cb1, flag1 = create_action()
    create_entry('t1', 20, 2, None, None, cb1.__name__)
    s = test_scheduler
    s.run(blocking=False)
    assert not flag1.is_set()
    # Move ahead to simulate the hi-pri task having taken ~3 ticks to complete.
    # Since hi-pri has an `interval` of 3, it should be re-queued to run again,
    # but low-pri should also be in the queue. If the scheduling algorithm is
    # too simplistic, the second hi-pri task will keep the low-pri task from
    # running, which is called "task starvation".
    advance_testclock(s.timefn, 4)
    s.run(blocking=False)
    assert flag1.is_set()


@pytest.mark.django_db
def test_task_pushed_past_stop_still_runs(test_scheduler):
    """A task pushed past `stop` by a long running task should still run."""
    # create an entry that runs at time 1 and 2
    cb0, flag0 = create_action()
    create_entry('t0', 10, 1, 3, 1, cb0.__name__)

    s = test_scheduler
    s.run(blocking=False)

    # simulate a long-running task that blocked until t=4
    advance_testclock(s.timefn, 4)
    s.run(blocking=False)
    # ensure that task ran at least once even though we're past its stop time
    assert flag0.is_set()


def test_str():
    str(Scheduler())
