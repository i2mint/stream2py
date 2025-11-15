"""Tests for using readers without context manager (Issue #18)"""
import pytest
from stream2py import StreamBuffer
from stream2py.tests.utils_for_testing import SimpleSourceReader
from stream2py.exceptions import StreamNotStartedError


def test_mk_reader_requires_started_buffer():
    """Test that mk_reader() raises clear error if buffer not started"""
    source = SimpleSourceReader(range(10))
    buffer = StreamBuffer(source, maxlen=100)

    # Trying to make a reader before starting should raise StreamNotStartedError
    with pytest.raises(StreamNotStartedError, match="StreamBuffer must be started"):
        buffer.mk_reader()


def test_reader_works_without_context_manager():
    """Test that BufferReader works without entering context manager"""
    source = SimpleSourceReader(range(10))

    buffer = StreamBuffer(source, maxlen=100)
    buffer.start()  # Must start before making reader

    # Create reader without using 'with' block
    reader = buffer.mk_reader()

    # Reading should work fine without context manager
    import time
    time.sleep(0.1)  # Let some data accumulate

    item = reader.read(ignore_no_item_found=True)
    assert item is not None

    # Can read multiple times
    item2 = reader.read(ignore_no_item_found=True)
    assert item2 is not None

    # Clean up
    buffer.stop()


def test_context_manager_ensures_cleanup():
    """Test that using context manager ensures proper cleanup for StreamSource"""
    from stream2py.examples.stream_source import SimpleCounterString

    source = SimpleCounterString(start=0, stop=10)

    # Using context manager ensures onclose is called
    with source.open_reader() as reader:
        item = reader.read()
        assert item is not None
        # When exiting, onclose will be called

    # After context exits, the reader is properly cleaned up
    # (open_readers count is decremented)


def test_reader_without_context_still_works():
    """Test that reader works without context but won't auto-cleanup"""
    from stream2py.examples.stream_source import SimpleCounterString

    source = SimpleCounterString(start=0, stop=10)

    # Create reader without context manager
    reader = source.open_reader()

    # Reading still works
    item = reader.read()
    assert item is not None

    item2 = reader.read()
    assert item2 is not None

    # Manually close the reader for cleanup
    reader.close()


def test_stream_buffer_with_context():
    """Test recommended pattern: StreamBuffer with context manager"""
    source = SimpleSourceReader(range(10))

    # Recommended: use StreamBuffer with context manager
    with StreamBuffer(source, maxlen=100) as buffer:
        reader = buffer.mk_reader()

        import time
        time.sleep(0.1)

        item = reader.read(ignore_no_item_found=True)
        assert item is not None
        # Buffer will auto-stop when context exits
