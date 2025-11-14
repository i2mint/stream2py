"""Tests for BufferReader blocking parameter"""
import time
import threading
from stream2py import StreamBuffer
from stream2py.tests.utils_for_testing import SimpleSourceReader
from itertools import count


def test_buffer_reader_blocking():
    """Test that blocking parameter works correctly for BufferReader.read()"""
    # Create a source with enough data
    source = SimpleSourceReader(range(100))

    with StreamBuffer(source, maxlen=100) as buffer:
        reader = buffer.mk_reader()

        # Wait a moment for some data to be available
        time.sleep(0.2)

        # Non-blocking read should return data immediately when available
        result = reader.read(blocking=False, ignore_no_item_found=True)
        assert result is not None, "Non-blocking read should return data"

        # Read a few more items with blocking=False
        for _ in range(3):
            result = reader.read(blocking=False, ignore_no_item_found=True)
            assert result is not None

        # Read with blocking=True should also work when data is available
        result = reader.read(blocking=True)
        assert result is not None, "Blocking read should return data when available"

        # Create a second reader that starts with no data yet read
        reader2 = buffer.mk_reader()

        # The second reader should be able to read with blocking=True
        result = reader2.read(blocking=True)
        assert result is not None, "Blocking read from new reader should get data"


def test_buffer_reader_blocking_stops_on_stop_event():
    """Test that blocking read returns None when buffer is stopped"""
    source = SimpleSourceReader(range(5))

    buffer = StreamBuffer(source, maxlen=100)
    buffer.start()
    reader = buffer.mk_reader()

    # Read all available data
    time.sleep(0.1)
    while reader.read(blocking=False, ignore_no_item_found=True) is not None:
        pass

    results = []

    def blocking_read_after_stop():
        # This should return None when buffer stops
        result = reader.read(blocking=True, ignore_no_item_found=False)
        results.append(result)

    # Start blocking read
    read_thread = threading.Thread(target=blocking_read_after_stop, daemon=True)
    read_thread.start()

    # Give it a moment to start blocking
    time.sleep(0.1)

    # Stop the buffer
    buffer.stop()

    # Wait for thread to complete
    read_thread.join(timeout=2)

    # Should have gotten None because buffer stopped
    assert len(results) == 1
    assert results[0] is None, "Blocking read should return None when stopped"
