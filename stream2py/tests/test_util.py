"""Testing the util.py module"""

from stream2py.util import contextualize_with_instance


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
        assert isinstance(e, AttributeError)
        assert e.args[0] == '__enter__'  # well yeah, reader doesn't have an __enter__!

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
