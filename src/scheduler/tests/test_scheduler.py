import time
import threading

import pytest

import actions
from authentication.models import User
from schedule.models import ScheduleEntry
from scheduler.scheduler import Scheduler, minimum_duration
from .utils import advance_testclock

def create_user(username):
    return User.objects.create_user(username)


def create_entry(name, priority, start, stop, interval, action):
    kwargs = {
        'name': name,
        'priority': priority,
        'stop': stop,
        'interval': interval,
        'action': action,
        'owner': create_user('test_scheduler_dummy_' + name)
    }

    if start is not None:
        kwargs['start'] = start

    return ScheduleEntry.objects.create(**kwargs)


def create_action():
    flag = threading.Event()
    cb = lambda entry, task_id: flag.set()  # noqa: E731
    cb.__name__ = 'testcb' + str(create_action.counter)
    actions.by_name[cb.__name__] = cb
    create_action.counter += 1
    return cb, flag


create_action.counter = 0


def create_bad_action():
    def bad_action():
        raise Exception

    actions.by_name['bad_action'] = bad_action
    return bad_action


@pytest.mark.django_db
def test_populate_queue(testclock):
    """An entry in the schedule should be added to a read-only task queue."""
    create_entry('test', 1, 0, 5, 1, 'logger')
    s = Scheduler()
    s.run(blocking=False)  # now=0, so task with time 0 is run
    assert [e.time for e in s.task_queue] == [1, 2, 3, 4]


@pytest.mark.django_db
def test_priority(testclock):
    """A task with lower priority number should sort higher in task queue."""
    lopri = 20
    hipri = 10
    create_entry('lopri', lopri, 0, 5, 1, 'logger')
    create_entry('hipri', hipri, 0, 5, 1, 'logger')
    s = Scheduler()
    s.run(blocking=False)
    q = s.task_queue.to_list()
    assert len(s.task_queue) == 8
    assert all(e.priority is hipri for e in q[::2])   # tasks at 0, 2...
    assert all(e.priority is lopri for e in q[1::2])  # tasks at 1, 3...


@pytest.mark.django_db
def test_future_start(testclock):
    """An entry with start time in future should remain in schedule."""
    create_entry('t', 1, 50, 100, 1, 'logger')
    s = Scheduler()
    s.run(blocking=False)
    assert len(s.task_queue) == 0
    assert len(s.schedule) == 1


@pytest.mark.django_db
def test_calls_actions(testclock):
    """The scheduler should call task's action function at the right time."""
    # This test works by registering a few test actions and ensuring the
    # scheduler calls them.
    test_actions = dict(create_action() for _ in range(3))

    for i, cb in enumerate(test_actions):
        create_entry('test' + str(i), 1, 0, 3, 1, cb.__name__)

    s = Scheduler()
    s.run(blocking=False)
    advance_testclock(s.timefn, 5)
    assert s.timefn() == 5
    s.run(blocking=False)
    flags = test_actions.values()
    assert all([flag.is_set() for flag in flags])
    assert not s.running


@pytest.mark.django_db
def test_add_entry(testclock):
    """Creating a new entry instance adds it to the current schedule."""
    create_entry('t1', 10, 1, 100, 5, 'logger')
    s = Scheduler()
    s.run(blocking=False)
    advance_testclock(s.timefn, 49)
    create_entry('t2', 20, 50, 300, 5, 'logger')
    s.run(blocking=False)
    assert len(s.task_queue) == 20
    assert s.task_queue[0].priority == 20


@pytest.mark.django_db
def test_remove_entry_by_delete(testclock):
    """An entry is removed from schedule if it's deleted."""
    e1 = create_entry('t1', 10, 1, 300, 5, 'logger')
    e2 = create_entry('t2', 20, 50, 300, 5, 'logger')
    s = Scheduler()
    s.run(blocking=False)
    advance_testclock(s.timefn, 10)
    e1.delete()
    s.run(blocking=False)
    assert len(s.schedule) == 1
    assert e2 in s.schedule


@pytest.mark.django_db
def test_remove_entry_by_cancel(testclock):
    """scheduler.cancel removes an entry from schedule without deleting it."""
    e1 = create_entry('t1', 10, 1, 300, 5, 'logger')
    e2 = create_entry('t2', 20, 50, 300, 5, 'logger')
    s = Scheduler()
    s.run(blocking=False)
    advance_testclock(s.timefn, 10)
    s.cancel(e1)
    s.run(blocking=False)
    assert len(s.schedule) == 1
    assert e2 in s.schedule


@pytest.mark.django_db(transaction=True)
def test_start_stop(testclock):
    """Calling stop on started scheduler thread should cause thread exit."""
    create_entry('t', 1, 1, 100, 5, 'logger')
    s = Scheduler()
    s.start()
    time.sleep(0.02)  # hit minimum_duration
    advance_testclock(s.timefn, 1)
    s.stop()
    advance_testclock(s.timefn, 1)
    s.join()
    assert not s.running


@pytest.mark.django_db(transaction=True)
def test_run_completes(testclock):
    """The scheduler should return to idle state after schedule completes."""
    create_entry('t', 1, None, None, None, 'logger')
    s = Scheduler()
    s.start()
    time.sleep(0.1)  # hit minimum_duration
    advance_testclock(s.timefn, 1)
    time.sleep(0.1)
    assert not s.running
    s.stop()
    advance_testclock(s.timefn, 1)
    s.join()


@pytest.mark.django_db
def test_survives_failed_action(testclock):
    """An action throwing an exception should be survivable."""
    cb1 = create_bad_action()
    create_entry('t1', 10, None, None, None, cb1.__name__)
    cb2, flag = create_action()
    # less priority to force run after bad_entry fails
    create_entry('t2', 20,  None, None, None, cb2.__name__)
    s = Scheduler()
    s.run(blocking=False)
    assert flag.is_set()


@pytest.mark.django_db
def test_compress_past_times(testclock):
    """Multiple task times in the past should be compressed to one."""
    create_entry('t', 1, -10, 5, 1, 'logger')
    s = Scheduler()
    s.run(blocking=False)
    # past times -10 through 0 are compressed and a single task is run,
    # then 1, 2, 3, and 4 are queued
    assert len(s.task_queue) == 4


@pytest.mark.django_db
def test_compress_past_times_offset(testclock):
    """Multiple task times in the past should be compressed to one."""
    create_entry('t', 1, -2, 14, 4, 'logger')
    s = Scheduler()
    s.run(blocking=False)
    # past time -2 is run, then 2, 6, and 10 are queued
    # NOTE: time 14 isn't included because range is [-2, 14) interval 4
    assert len(s.task_queue) == 3


# XXX: refactor
@pytest.mark.django_db
def test_next_task_time_value_when_start_changes(testclock):
    entry = create_entry('t', 1, 1, 10, 1, 'logger')
    s = Scheduler()
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
def test_next_task_time_value_when_interval_changes(testclock):
    entry = create_entry('t', 1, 1, 100, 1, 'logger')
    s = Scheduler()
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
def test_one_shot(testclock):
    """If no start or interval given, entry should be run once and removed."""
    create_entry('t', 1, None, None, None, 'logger')
    s = Scheduler()
    s.run(blocking=False)
    assert len(s.task_queue) == 0
    assert not s.schedule_has_entries


@pytest.mark.django_db
def test_task_queue(testclock):
    e = create_entry('t', 1, 1, 100, 5, 'logger')
    s = Scheduler()

    # upcoming tasks are queued
    s.run(blocking=False)  # queue first 10 tasks
    assert len(s.task_queue) == 10

    # task queue is purely informational, IOW, adding tasks to task queue
    # doesn't consume them from the entry
    advance_testclock(s.timefn, 10)
    s.run(blocking=False)  # consume 2 tasks and queue 2 more tasks
    assert len(s.task_queue) == 10
    e.refresh_from_db()
    assert len(e.get_remaining_times()) == 100/5 - 2

    # canceled tasks are removed from task queue
    s.cancel(e)
    s.run(blocking=False)
    assert len(s.task_queue) == 0
    assert len(s.schedule) == 0


@pytest.mark.django_db
def test_clearing_schedule_clears_task_queue(testclock):
    """The scheduler should empty task_queue when schedule is deleted."""
    create_entry('t', 1, 1, 100, 5, 'logger')
    s = Scheduler()
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


def test_str():
    str(Scheduler())
