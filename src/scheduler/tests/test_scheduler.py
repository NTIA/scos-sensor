import time
import threading

import pytest

import actions
from scheduler.models import ScheduleEntry
from scheduler.scheduler import Scheduler
from .utils import advance_testclock


def create_entry(name, priority, start, stop, interval, action):
    kwargs = {
        'name': name,
        'priority': priority,
        'stop': stop,
        'interval': interval,
        'action': action
    }

    if start is not None:
        kwargs['start'] = start

    return ScheduleEntry.objects.create(**kwargs)


def create_action():
    flag = threading.Event()
    cb = lambda edid, eid: flag.set()  # noqa: E731
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
def test_populates_queue(testclock):
    create_entry('test', 1, 0, 5, 1, 'logger')
    s = Scheduler()
    s.run(blocking=False)  # now=0, so task with time 0 is run
    assert [e.time for e in s.task_queue] == [1, 2, 3, 4]


@pytest.mark.django_db
def test_priority(testclock):
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
    """Don't remove an entry that starts in the future"""
    create_entry('t', 1, 50, 100, 1, 'logger')
    s = Scheduler()
    s.run(blocking=False)
    assert len(s.task_queue) == 0
    assert len(s.schedule) == 1


@pytest.mark.django_db
def test_calls_actions(testclock):
    """Register a few test actions and ensure the scheduler calls them."""
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
    create_entry('t1', 10, 1, 100, 5, 'logger')
    s = Scheduler()
    s.run(blocking=False)
    advance_testclock(s.timefn, 49)
    create_entry('t2', 20, 50, 300, 5, 'logger')
    s.run(blocking=False)
    assert len(s.task_queue) == 20
    assert s.task_queue[0].priority == 20


@pytest.mark.django_db
def test_remove_entry(testclock):
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
def test_start_stop(testclock):
    create_entry('t', 1, 1, 100, 5, 'logger')
    s = Scheduler()
    s.start()
    time.sleep(0.02)  # hit delayfn
    s.stop()
    s.join()
    assert not s.running


@pytest.mark.django_db
def test_run_completes(testclock):
    create_entry('t', 1, None, None, None, 'logger')
    s = Scheduler()
    s.start()
    time.sleep(0.1)
    assert s.running is False
    s.stop()
    s.join()


@pytest.mark.django_db
def test_survives_failed_action(testclock):
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
    create_entry('t', 1, -10, 5, 1, 'logger')
    s = Scheduler()
    s.run(blocking=False)
    # past times -10 through 0 are compressed and a single task is run,
    # then 1, 2, 3, and 4 are queued
    assert len(s.task_queue) == 4


@pytest.mark.django_db
def test_compress_past_times_offset(testclock):
    create_entry('t', 1, -2, 14, 4, 'logger')
    s = Scheduler()
    s.run(blocking=False)
    # past time -2 is run, then 2, 6, and 10 are queued
    # NOTE: time 14 isn't included because range is [-2, 14) interval 4
    assert len(s.task_queue) == 3


@pytest.mark.django_db
def test_one_shot(testclock):
    create_entry('t', 1, None, None, None, 'logger')
    s = Scheduler()
    s.run(blocking=False)
    assert len(s.task_queue) == 0
    assert len(s.schedule) == 0


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
def test_clear_schedule_clears_task_queue(testclock):
    create_entry('t', 1, 1, 100, 5, 'logger')
    s = Scheduler()

    s.run(blocking=False)  # queue first 10 tasks
    assert len(s.task_queue) == 10

    s.schedule.delete()

    s.run(blocking=False)
    assert len(s.task_queue) == 0


def test_str():
    str(Scheduler())
