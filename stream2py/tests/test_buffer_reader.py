from itertools import count

from stream2py.buffer_reader import BufferReader
from stream2py.tests.utils_for_testing import SimpleSourceReader


def test_inject_buffer_reader():
    """Test injecting custom buffer reader"""
    test_msg = 'test_msg'

    class TestBufferReader(BufferReader):
        def custom_function(self):
            return test_msg

    class TestSourceReader(SimpleSourceReader):
        buffer_reader_class = TestBufferReader

    source = TestSourceReader(count())
    with source.stream_buffer(10) as buffer:
        reader = buffer.mk_reader()
        assert isinstance(reader, TestBufferReader)
        assert reader.custom_function() is test_msg


def test_range_join_trims_and_joins_chunks():
    """i2mint/stream2py#14: range(join=True) returns the exact span as one item."""
    import pytest
    from stream2py import SourceReader, StreamBuffer

    class Chunks(SourceReader):
        """Items are (first_key, [values...]); value i sits at key first_key + i."""

        def __init__(self, size=4, n=5):
            self.size, self.n = size, n

        def open(self):
            self._it = iter(range(self.n))

        def read(self):
            i = next(self._it, None)
            if i is None:
                return None
            return (i * self.size, list(range(i * self.size, (i + 1) * self.size)))

        def close(self):
            pass

        def key(self, data):
            return data[0]

        def slice_item(self, item, start=None, stop=None):
            first, values = item
            lo = 0 if start is None else max(start - first, 0)
            hi = len(values) if stop is None else stop - first + 1
            return (first + lo, values[lo:hi])

        def join_items(self, items):
            return (items[0][0], [v for _, vs in items for v in vs])

    class NoJoin(Chunks):
        slice_item = SourceReader.slice_item
        join_items = SourceReader.join_items

    import time

    with StreamBuffer(source_reader=Chunks(), maxlen=10) as sb:
        reader = sb.mk_reader()
        time.sleep(0.3)
        assert reader.range(6, 13, join=True) == (6, list(range(6, 14)))
        assert reader.last_key == 12  # cursor stays on a real buffer item
        assert reader.range(5, 5, join=True, peek=True) == (5, [5])
        assert reader.range(0, 19, join=True) == (0, list(range(20)))
        # default behaviour is unchanged: whole chunks, from the first key >= start
        assert [k for k, _ in reader.range(6, 13)] == [8, 12]
        with pytest.raises(ValueError):
            reader.range(0, 5, step=2, join=True)

    with StreamBuffer(source_reader=NoJoin(), maxlen=10) as sb:
        reader = sb.mk_reader()
        with pytest.raises(NotImplementedError):
            reader.range(0, 5, join=True)
