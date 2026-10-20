"""range(join=True) (i2mint/stream2py#14).

Deliberately thread-free: the buffer and reader are driven directly, so these tests
can't compete for CPU with the timing-sensitive threaded tests around them."""
import threading

import pytest

from stream2py import SourceReader
from stream2py.stream_buffer import _SourceBuffer, _overridden


class Chunks(SourceReader):
    """Items are (first_key, [values...]); value i sits at key first_key + i."""

    def open(self):
        pass

    def read(self):
        return None

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


def _reader(source, n=5, size=4):
    sb = _SourceBuffer(
        {},
        threading.Event(),
        key=source.key,
        join_items=_overridden(source, "join_items"),
        slice_item=_overridden(source, "slice_item"),
    )
    for i in range(n):
        sb.append((i * size, list(range(i * size, (i + 1) * size))))
    return sb.mk_reader()


def test_range_join_trims_and_joins_chunks():
    reader = _reader(Chunks())
    assert reader.range(6, 13, join=True) == (6, list(range(6, 14)))
    assert reader.last_key == 12  # cursor stays on a real buffer item
    assert reader.range(5, 5, join=True, peek=True) == (5, [5])
    assert reader.range(0, 19, join=True) == (0, list(range(20)))
    # default behaviour is unchanged: whole chunks, from the first key >= start
    assert [k for k, _ in reader.range(6, 13)] == [8, 12]
    with pytest.raises(ValueError):
        reader.range(0, 5, step=2, join=True)


def test_range_join_only_new_items_starts_after_cursor():
    reader = _reader(Chunks())
    reader.range(0, 5)  # cursor now on the chunk with key 4
    assert reader.last_key == 4
    assert reader.range(0, 13, join=True, only_new_items=True)[0] == 8


def test_range_join_needs_the_source_to_implement_it():
    assert _overridden(NoJoin(), "join_items") is None
    with pytest.raises(NotImplementedError):
        _reader(NoJoin()).range(0, 5, join=True)
