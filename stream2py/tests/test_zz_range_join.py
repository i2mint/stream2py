"""range(join=True) (i2mint/stream2py#14). Named test_zz_ so it runs last: its
threaded sources must not compete with the timing-sensitive tests before it."""

def _chunks_source_class():
    import time

    from stream2py import SourceReader

    class Chunks(SourceReader):
        """Items are (first_key, [values...]); value i sits at key first_key + i."""

        def __init__(self, size=4, n=5):
            self.size, self.n = size, n

        def open(self):
            self._it = iter(range(self.n))

        def read(self):
            i = next(self._it, None)
            if i is None:
                time.sleep(0.01)  # don't spin the reader thread once exhausted
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

    return Chunks


def test_range_join_trims_and_joins_chunks():
    """i2mint/stream2py#14: range(join=True) returns the exact span as one item."""
    import pytest
    from stream2py import SourceReader, StreamBuffer

    Chunks = _chunks_source_class()

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


def test_range_join_only_new_items_starts_after_cursor():
    import time

    from stream2py import StreamBuffer

    with StreamBuffer(source_reader=_chunks_source_class()(), maxlen=10) as sb:
        reader = sb.mk_reader()
        time.sleep(0.3)
        reader.range(0, 5)  # cursor now on the chunk with key 4
        assert reader.last_key == 4
        joined = reader.range(0, 13, join=True, only_new_items=True)
        assert joined[0] == 8  # nothing at or before the cursor chunk is repeated
