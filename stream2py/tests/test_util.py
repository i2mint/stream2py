"""Testing the util.py module"""

import pytest

from stream2py.util import contextualize_with_instance, Timer


class StreamHasNotBeenStarted(RuntimeError):
    """Raised when an action requires the stream to be 'on'"""


class Streamer:
    def __init__(self, iterable):
        self.iterable = iterable
        self.is_running = False
        self._read = None

    def enter(self):
        #         print(f'{type(self).__name__}.enter')
        self._read = iter(self.iterable).__next__
        self.is_running = True

    def exit(self, *exc):
        #         print(f'{type(self).__name__}.exit')
        self._read = None
        self.is_running = False

    __enter__, __exit__ = enter, exit

    def read(self):
        if not self.is_running:
            raise StreamHasNotBeenStarted(
                'The stream needs to be on/started (in a context) for that!'
            )
        return self._read()


def test_test_objects():
    """This test tests the test objects themselves, to make sure they have the
    expected behavior, commenting at the same time on what kind of behavior we'd
    like to have the power to create, which we get through contextualize_with_instance
    """
    # Testing the test objects

    s = Streamer('stream')

    # demo
    with s:
        assert s.read() == 's'
        assert s.read() == 't'

    # a reader test function
    def test_reader(reader):
        assert ''.join(reader() for _ in range(6)) == 'stream'

    # Normal case: With a context

    reader = s.read

    with s:
        test_reader(reader)

    # Normal case: Manual entering/exiting

    s.enter()
    reader = s.read
    test_reader(reader)
    s.exit()

    # But if we don't turn things on...

    reader = s.read
    try:
        # oops, forgot the enter s context
        test_reader(reader)
        it_worked = True
    except StreamHasNotBeenStarted as e:
        it_worked = False
        assert isinstance(e, StreamHasNotBeenStarted)
        assert e.args[0] == 'The stream needs to be on/started (in a context) for that!'
    assert not it_worked

    # But we can't turn the read method on -- it's not a context (it's instance is!)

    reader = s.read

    try:
        with reader:  # can we actually do this (answer: no! We can enter s, not s.read)
            test_reader(reader)
        it_worked = True
    except Exception as e:
        it_worked = False
        # Python 3.11+ raises TypeError instead of AttributeError for context manager protocol
        assert isinstance(e, (AttributeError, TypeError))
        if isinstance(e, AttributeError):
            assert e.args[0] == '__enter__'  # well yeah, reader doesn't have an __enter__!
        else:  # TypeError
            assert 'context manager' in str(e)

    assert not it_worked

    # But with contextualize_with_instance, you can
    # (see test_contextualize_with_instance)


def test_contextualize_with_instance():
    """To understand the context of this test, the reader should consider the
    test_test_objects, or even better, see:

    issue: https://github.com/i2mint/stream2py/issues/18

    wiki: https://github.com/i2mint/stream2py/wiki/Forwarding-context-management

    """
    s = Streamer('stream')

    # a reader test function
    def test_reader(reader):
        assert ''.join(reader() for _ in range(6)) == 'stream'

    reader = contextualize_with_instance(s.read)

    try:
        with reader:  # now we can enter the reader!
            test_reader(reader)
        it_worked = True
    except Exception as e:
        it_worked = False

    assert it_worked  # Hurray!


# ---------------------------------------------------------------------------------------
# Timer


def test_timer_manual_start_stop():
    """A manually started timer reports a positive, monotonically growing elapsed time."""
    timer = Timer()
    timer.start()
    first = timer.elapsed()
    assert first >= 0
    second = timer.elapsed()
    assert second >= first  # monotonic clock: never goes backwards
    timer.stop()


def test_timer_as_context_manager():
    """Entering the context starts the timer and yields the timer itself."""
    with Timer() as timer:
        assert isinstance(timer, Timer)
        assert timer.elapsed() >= 0
    # leaving the context stops it
    assert timer.start_time is None


def test_timer_egress_is_applied():
    """The egress function transforms the elapsed seconds."""
    with Timer(lambda seconds: 'transformed') as timer:
        assert timer.elapsed() == 'transformed'


def test_timer_is_reusable_across_contexts():
    """The same instance can be re-entered after being stopped."""
    timer = Timer()
    with timer:
        pass
    assert timer.start_time is None
    with timer:
        assert timer.elapsed() >= 0
    assert timer.start_time is None


def test_timer_elapsed_before_start_raises_informatively():
    """Asking a stopped timer for elapsed time raises ValueError, not TypeError.

    This is the regression guard for the original implementation, which detected the
    not-started case by catching TypeError from ``time() - None``. That conflated "timer
    not started" with "egress itself raised TypeError" -- see the test below.
    """
    with pytest.raises(ValueError, match='not running'):
        Timer().elapsed()


def test_timer_does_not_swallow_egress_errors():
    """An exception raised by egress propagates, rather than being silently dropped.

    The original implementation wrapped the whole computation in ``try/except TypeError``
    and, when ``start_time`` was not None, fell off the end of the function -- returning
    None and hiding the real error.
    """

    def broken_egress(seconds):
        raise TypeError('egress is broken')

    with Timer(broken_egress) as timer:
        with pytest.raises(TypeError, match='egress is broken'):
            timer.elapsed()


def test_timer_stop_accepts_context_manager_exit_args():
    """__exit__ is stop(), so it must tolerate the (exc_type, exc, tb) triple."""
    timer = Timer().start()
    timer.stop(ValueError, ValueError('x'), None)
    assert timer.start_time is None
