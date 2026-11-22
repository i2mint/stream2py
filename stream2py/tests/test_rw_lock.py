"""Tests for the readers-writer lock: shared reads, exclusive writes (deterministic, no sleeps)."""

import threading

from stream2py.utility.reader_writer_lock import RWLock

WAIT = (
    5.0  # generous upper bound; every wait below is released by an event, not by time
)


def _in_thread(fn):
    done = threading.Event()

    def run():
        fn()
        done.set()

    threading.Thread(target=run, daemon=True).start()
    return done


def test_many_readers_hold_the_lock_at_once():
    lock = RWLock()
    lock.reader_acquire()
    second = _in_thread(lambda: (lock.reader_acquire(), lock.reader_release()))
    assert second.wait(WAIT), "a second reader must not block while a reader holds"
    lock.reader_release()


def test_a_writer_waits_for_the_last_reader():
    lock = RWLock()
    lock.reader_acquire()
    wrote = _in_thread(lambda: (lock.writer_acquire(), lock.writer_release()))
    assert not wrote.wait(0.2), "a writer must wait while a reader holds"
    lock.reader_release()
    assert wrote.wait(WAIT)


def test_a_reader_waits_for_the_writer():
    lock = RWLock()
    lock.writer_acquire()
    read = _in_thread(lambda: (lock.reader_acquire(), lock.reader_release()))
    assert not read.wait(0.2), "a reader must wait while a writer holds"
    lock.writer_release()
    assert read.wait(WAIT)


def test_writers_exclude_each_other():
    lock = RWLock()
    lock.writer_acquire()
    other = _in_thread(lambda: (lock.writer_acquire(), lock.writer_release()))
    assert not other.wait(0.2)
    lock.writer_release()
    assert other.wait(WAIT)
