"""Tests for ``mk_stream_buffer``: open/close wiring, enumeration, key and info seams."""

import itertools

from stream2py.simply import mk_stream_buffer
from stream2py.tests.utils_for_testing import wait_until


def _finite(n):
    it = iter(range(n))
    return lambda open_inst: next(it, None)


def test_open_and_close_are_called_once_and_data_is_enumerated():
    events = []
    with mk_stream_buffer(
        read_stream=_finite(5),
        open_stream=lambda: events.append("open") or "handle",
        close_stream=lambda inst: events.append(("close", inst)),
        sleep_time_on_read_none_seconds=0.01,
        maxlen=None,
    ) as buf:
        assert wait_until(lambda: len(buf.source_buffer) >= 5)
        items = buf.mk_reader().read(n=5, ignore_no_item_found=True)
    assert [i for i, _ in items] == [0, 1, 2, 3, 4]
    assert [d for _, d in items] == [0, 1, 2, 3, 4]
    # closing happens on the buffer thread as it winds down: wait for it, don't assume
    assert wait_until(lambda: len(events) == 2)
    assert events == ["open", ("close", "handle")]


def test_enumerate_data_false_keeps_raw_items_and_key_orders_them():
    with mk_stream_buffer(
        read_stream=_finite(4),
        enumerate_data=False,
        key=lambda x: x,
        sleep_time_on_read_none_seconds=0.01,
        maxlen=None,
    ) as buf:
        assert wait_until(lambda: len(buf.source_buffer) >= 4)
        reader = buf.mk_reader()
        assert reader.read(n=4, ignore_no_item_found=True) == [0, 1, 2, 3]


def test_default_info_reports_open_time_and_instance_and_custom_info_wins():
    with mk_stream_buffer(
        read_stream=_finite(1),
        open_stream=lambda: "inst",
        sleep_time_on_read_none_seconds=0.01,
    ) as buf:
        info = buf.mk_reader().source_reader_info
        assert info["open_instance"] == "inst" and info["open_time"] > 0
    with mk_stream_buffer(
        read_stream=_finite(1),
        open_stream=lambda: "inst",
        info=lambda inst: {"custom": inst},
        sleep_time_on_read_none_seconds=0.01,
    ) as buf:
        assert buf.mk_reader().source_reader_info == {"custom": "inst"}


def test_without_open_or_close_callbacks_the_stream_still_runs():
    counter = itertools.count()
    with mk_stream_buffer(
        read_stream=lambda inst: next(counter) if next(counter) < 3 else None,
        sleep_time_on_read_none_seconds=0.01,
    ) as buf:
        assert wait_until(lambda: len(buf.source_buffer) >= 1)
