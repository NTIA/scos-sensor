import time
import threading

import actions
from commsensor.events import ScheduleEntry
from scheduler.scheduler import Scheduler
from .utils import advance_testclock


def _entry_factory(id, pri, start, stop, step, cb):
    e = ScheduleEntry(id=id, priority=pri, start=start, stop=stop,
                      interval=step, action_name=cb)
    return e


def _scheduler_factory(entriess):
    s = Scheduler()
    db.session.add_all(entriess)
    db.session.commit()
    return s


def create_action():
    flag = threading.Event()
    cb = lambda edid, eid: flag.set()  # noqa: E731
    cb.__name__ = 'testcb' + str(create_action.counter)
    actions.by_name[cb.__name__] = cb
    create_action.counter += 1
    return cb, flag


create_action.counter = 0


def test_populates_queue(app, testclock):
    e1 = _entry_factory('test', 1, 0, 5, 1, 'logger')
    s = _scheduler_factory([e1])
    s.run(blocking=False)  # now=0, so event with time 0 is run
    assert [e.time for e in s.event_queue] == [1, 2, 3, 4]


def test_priority(app, testclock):
    lopri = 20
    hipri = 10
    e1 = _entry_factory('lopri', lopri, 0, 5, 1, 'logger')
    e2 = _entry_factory('hipri', hipri, 0, 5, 1, 'logger')
    s = _scheduler_factory([e1, e2])
    s.run(blocking=False)
    q = s.event_queue.to_list()
    assert len(s.event_queue) == 8
    assert all(e.priority is hipri for e in q[::2])   # events at 0, 2...
    assert all(e.priority is lopri for e in q[1::2])  # events at 1, 3...


def test_future_start(app, testclock):
    """Don't remove an event descriptor that starts in the future"""
    e = _entry_factory('t', 1, 50, 100, 1, 'logger')
    s = _scheduler_factory([e])
    s.run(blocking=False)
    assert len(s.event_queue) == 0
    assert len(s.schedule) == 1


def test_calls_actions(app, testclock):
    """Register a few test actions and ensure the scheduler calls them."""
    test_actions = dict(create_action() for _ in range(3))

    entrys = []
    for i, cb in enumerate(test_actions):
        e = _entry_factory('test' + str(i), 1, 0, 3, 1, cb.__name__)
        entrys.append(e)

    s = _scheduler_factory(entrys)
    s.run(blocking=False)
    advance_testclock(s.timefn, 5)
    assert s.timefn() == 5
    s.run(blocking=False)
    flags = test_actions.values()
    assert all([flag.is_set() for flag in flags])
    assert not s.running


def test_add_entry(app, testclock):
    e1 = _entry_factory('t1', 10, 1, 100, 5, 'logger')
    s = _scheduler_factory([e1])
    s.run(blocking=False)
    advance_testclock(s.timefn, 49)
    e2 = _entry_factory('t2', 20, 50, 300, 5, 'logger')
    db.session.add(e2)
    db.session.commit()
    s.run(blocking=False)
    assert len(s.event_queue) == 20
    assert s.event_queue[0].priority == 20


def test_remove_entry(app, testclock):
    e1 = _entry_factory('t1', 10, 1, 300, 5, 'logger')
    e2 = _entry_factory('t2', 20, 50, 300, 5, 'logger')
    s = _scheduler_factory([e1, e2])
    s.run(blocking=False)
    advance_testclock(s.timefn, 10)
    db.session.delete(e1)
    db.session.commit()
    s.run(blocking=False)
    assert len(s.schedule) == 1
    assert e2 in s.schedule


def test_start_stop(app, testclock):
    e = _entry_factory('t', 1, 1, 100, 5, 'logger')
    s = _scheduler_factory([e])
    s.start()
    time.sleep(0.02)  # hit delayfn
    s.stop()
    s.join()
    assert not s.running


def test_run_completes(app, testclock):
    e = _entry_factory('t', 1, None, None, None, 'logger')
    s = _scheduler_factory([e])
    s.start()
    time.sleep(0.1)
    assert s.running is False
    s.stop()
    s.join()


def test_survives_failed_test(app, testclock):
    bad_entry = ScheduleEntry(id='t1', priority=10,
                            action_name='logger',
                            action_parameters={"doesntexist": False})
    cb, flag = create_action()
    # "lower" priority to force run after bad_entry fails
    good_entry = _entry_factory('t2', 20,  None, None, None, cb.__name__)
    s = _scheduler_factory([bad_entry, good_entry])
    s.run(blocking=False)
    assert flag.is_set()


def test_compress_past_times(app, testclock):
    e = _entry_factory('t', 1, -10, 5, 1, 'logger')
    s = _scheduler_factory([e])
    s.run(blocking=False)
    # past times -10 through 0 are compressed and a single event is run,
    # then 1, 2, 3, and 4 are queued
    assert len(s.event_queue) == 4


def test_compress_past_times_offset(app, testclock):
    e = _entry_factory('t', 1, -2, 14, 4, 'logger')
    s = _scheduler_factory([e])
    s.run(blocking=False)
    # past time -2 is run, then 2, 6, and 10 are queued
    # NOTE: time 14 isn't included because range is [-2, 14) interval 4
    assert len(s.event_queue) == 3


def test_one_shot(app, testclock):
    e = _entry_factory('t', 1, None, None, None, 'logger')
    s = _scheduler_factory([e])
    s.run(blocking=False)
    assert len(s.event_queue) == 0
    assert len(s.schedule) == 0


def test_event_queue(app, testclock):
    e = _entry_factory('t', 1, 1, 100, 5, 'logger')
    s = _scheduler_factory([e])

    # upcoming events are queued
    s.run(blocking=False)  # queue first 10 events
    assert len(s.event_queue) == 10

    # event queue is purely informations, IOW, adding events to event queue
    # doesn't consume them from the event descriptor
    advance_testclock(s.timefn, 10)
    s.run(blocking=False)  # consume 2 events and queue 2 more events
    assert len(s.event_queue) == 10
    assert len(e.get_remaining_times()) == 100/5 - 2

    # canceled events are removed from event queue
    s.cancel(e)
    s.run(blocking=False)
    assert len(s.event_queue) == 0
    assert len(s.schedule) == 0


def test_clear_schedule_clears_event_queue(app, testclock):
    e = _entry_factory('t', 1, 1, 100, 5, 'logger')
    s = _scheduler_factory([e])

    s.run(blocking=False)  # queue first 10 events
    assert len(s.event_queue) == 10

    for entry in s.schedule.copy():
        db.session.delete(entry)

    db.session.commit()

    s.run(blocking=False)
    assert len(s.event_queue) == 0


def test_str():
    str(Scheduler())
