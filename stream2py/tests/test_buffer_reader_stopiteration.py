"""Tests for BufferReader StopIteration behavior (Issue #10)"""
import pytest
from stream2py import StreamBuffer
from stream2py.tests.utils_for_testing import SimpleSourceReader


def test_next_raises_stopiteration_when_stopped():
    """Test that __next__() raises StopIteration when stream is stopped and no data available"""
    source = SimpleSourceReader(range(5))

    buffer = StreamBuffer(source, maxlen=100)
    buffer.start()
    reader = buffer.mk_reader()

    # Read some items using next()
    item1 = next(reader)
    assert item1 is not None

    item2 = next(reader)
    assert item2 is not None

    # Stop the buffer
    buffer.stop()

    # Now __next__() should raise StopIteration when called
    # (after any remaining buffered data is consumed)
    with pytest.raises(StopIteration):
        # Keep calling next until StopIteration is raised
        for _ in range(100):  # Safety limit
            next(reader)


def test_next_returns_none_when_no_data_but_running():
    """Test that __next__() returns None when no data available but stream still running"""
    source = SimpleSourceReader(range(10))

    with StreamBuffer(source, maxlen=100) as buffer:
        reader = buffer.mk_reader()

        # Read all available data quickly
        import time
        time.sleep(0.1)  # Let some data accumulate

        # Read until we get None (no more data available yet)
        items = []
        for _ in range(20):
            item = next(reader)
            if item is None:
                # Got None - stream is still running but no data yet
                assert not reader.is_stopped
                break
            items.append(item)

        # Should have gotten some items
        assert len(items) > 0


def test_builtin_next_with_default():
    """Test that builtin next() with default works correctly"""
    source = SimpleSourceReader(range(3))

    buffer = StreamBuffer(source, maxlen=100)
    buffer.start()
    reader = buffer.mk_reader()

    import time
    time.sleep(0.1)

    # Read items
    item1 = next(reader, 'default')
    assert item1 != 'default'

    item2 = next(reader, 'default')
    assert item2 != 'default'

    # Stop the buffer
    buffer.stop()

    # When stopped and no data, should raise StopIteration
    # and the default should be returned by builtin next()
    time.sleep(0.1)

    # Consume any remaining data
    while True:
        try:
            item = next(reader)
            if item is None:
                # No more data, try once more to trigger StopIteration
                continue
        except StopIteration:
            break

    # Now next with default should return the default
    result = next(reader, 'my_default')
    assert result == 'my_default'


def test_for_loop_stops_correctly():
    """Test that for loop over BufferReader stops correctly when stream ends"""
    source = SimpleSourceReader(range(10))

    buffer = StreamBuffer(source, maxlen=100)
    buffer.start()

    import time
    time.sleep(0.2)  # Let all data load

    buffer.stop()  # Stop before iterating

    reader = buffer.mk_reader()

    # For loop should exhaust the buffered data and then stop
    items = []
    for item in reader:
        if item is not None:
            items.append(item)
        if len(items) >= 20:  # Safety limit
            break

    # Should have gotten the buffered items
    assert len(items) > 0
