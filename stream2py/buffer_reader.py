__all__ = ['BufferReader']

import threading
import time
from contextlib import suppress

from stream2py.utility.locked_sorted_deque import RWLockSortedDeque
from stream2py.utility.typing_hints import Union


class BufferReader:
    """Reader that is constructed from StreamBuffer.mk_reader()

    >>> from stream2py import StreamBuffer, BufferReader
    >>> from stream2py.examples.source_reader import SimpleCounterString
    >>>
    >>> source_reader = SimpleCounterString(start=0, stop=100)
    >>> stream_buffer = StreamBuffer(source_reader=source_reader, maxlen=100)
    >>> stream_buffer.start()
    >>>
    >>> buffer_reader = stream_buffer.mk_reader()
    >>> isinstance(buffer_reader, BufferReader)
    True
    >>> buffer_reader.is_stopped
    False
    >>> buffer_reader.last_item == None  # None until value is seen
    True
    >>> buffer_reader.next() # get first item
    's0'
    >>> buffer_reader.last_item # check last_item cursor
    's0'
    >>> buffer_reader.next(peek=True), buffer_reader.last_item # next will not update last_item cursor
    ('s1', 's0')
    >>> buffer_reader.next(), buffer_reader.last_item # same as what was peeked but now cursor is updated
    ('s1', 's1')
    >>> buffer_reader.range(start=5, stop=10)
    ['s5', 's6', 's7', 's8', 's9', 's10']
    >>> buffer_reader.last_item
    's10'
    >>> buffer_reader.range(start=5, stop=10, step=3), buffer_reader.last_item
    (['s5', 's8'], 's8')
    >>> buffer_reader.range(start=10, stop=15, peek=True)
    ['s10', 's11', 's12', 's13', 's14', 's15']
    >>> buffer_reader.last_item # unchanged with peek
    's8'
    >>> buffer_reader.last_key # key of last_item
    8
    >>> buffer_reader.range(start=0, stop=9, only_new_items=True) # only 9 is greater than last item key
    ['s9']
    >>> buffer_reader.head(), buffer_reader.last_item, buffer_reader.last_key
    ('s0', 's0', 0)
    >>> buffer_reader.tail(), buffer_reader.last_item, buffer_reader.last_key
    ('s99', 's99', 99)
    >>>
    >>> stream_buffer.stop()
    >>>
    >>> buffer_reader.is_stopped
    True
    """

    def __init__(
        self,
        buffer: RWLockSortedDeque,
        source_reader_info: dict,
        stop_event: threading.Event,
    ):
        """

        :param buffer:
        :param source_reader_info:
        :param stop_event: threading.Event for source read loop
        """
        assert isinstance(buffer, RWLockSortedDeque)
        assert isinstance(stop_event, threading.Event)

        self._source_reader_info = source_reader_info
        self._buffer = buffer
        self._last_item = None
        self._last_key = None
        self._stop_event = stop_event
        self._sleep_time_on_iter_none_s = 0.1

    def __iter__(self):
        while True:
            _next = self.next(ignore_no_item_found=True)
            if _next is not None:
                yield _next
            elif self.is_stopped:
                return None
            else:
                time.sleep(self._sleep_time_on_iter_none_s)

    def __next__(self):
        return self.next(ignore_no_item_found=True)

    def set_sleep_time_on_iter_none(self, sleep_time_s: Union[int, float] = 0.1):
        """Set the sleep time of the iter yield loop when next data item is not yet available.

        :param sleep_time_s: seconds to sleep
        """
        self._sleep_time_on_iter_none_s = sleep_time_s

    def is_same_buffer(self, other_buffer_reader):
        """Check if reader is looking at the same buffer"""
        return (
            self.__class__ == other_buffer_reader.__class__
            and self._stop_event == other_buffer_reader._stop_event
        )

    @property
    def is_stopped(self) -> bool:
        """Checks if stop event has been set by StreamBuffer.

        :return: bool
        """
        return self._stop_event.is_set()

    @property
    def source_reader_info(self) -> dict:
        """A dict with important source info set by SourceReader.

        :return: dict
        """
        return self._source_reader_info

    @property
    def last_key(self):
        """key to last seen item cursor"""
        return self._last_key

    def _getlast_item(self):
        return self._last_item

    def _setlast_item(self, item):
        self._last_key = self._buffer.key(item)
        self._last_item = item

    def _dellast_item(self):
        del self._last_item
        self._last_item = None
        del self._last_key
        self._last_key = None

    last_item = property(
        _getlast_item, _setlast_item, _dellast_item, 'last seen item cursor'
    )

    def next(self, n=1, *, peek=False, ignore_no_item_found=False, strict_n=False):
        """Finds an item with a key greater than the last returned item.
        Raise ValueError if no item found with key above last item.

        :param n: number of items to return
        :param peek: if True, last_item cursor will not be updated
        :param ignore_no_item_found: if True, return None when no next item instead of raising exception
        :param strict_n: if True, raise ValueError if n items are not available
        :return: next item or list of next items if n > 1
        """
        with self._buffer.reader_lock() as reader:
            try:
                next_item = reader.find_gt(self.last_key)
            except ValueError as e:  # ValueError: No item found with key above: self.last_key
                if ignore_no_item_found:
                    return None
                else:
                    raise e
            except TypeError as e:  # TypeError: '<' not supported between instances of 'NoneType' and type(key)
                if self.last_item is None:  # first time reading a value from buffer
                    next_item = reader[0]
                else:
                    raise e
            if n > 1:
                i = reader.index(next_item)
                j = i + n
                if strict_n and j >= len(reader):
                    raise ValueError(
                        f'Number of items found is less than n: strict_n={strict_n}, n={n}'
                    )

                next_items_list = reader.range_by_index(i, j)
                if not peek:
                    self.last_item = next_items_list[-1]
                return next_items_list
            else:
                if not peek:
                    self.last_item = next_item
                return next_item

    def range(
        self,
        start,
        stop,
        step=None,
        *,
        peek=False,
        ignore_no_item_found=False,
        only_new_items=False,
        start_le=False,
        stop_ge=False,
    ):
        """Enables:
        1. Get last n minutes
        2. Give me data I don't have

        :param start: starting range key of item inclusive
        :param stop: ending range key of item inclusive
        :param step:
        :param peek: if True, last_item cursor will not be updated
        :param ignore_no_item_found: if True, return None when no next item instead of raising exception.
        :param only_new_items: if True and no new items, raise ValueError or return None if ignore_no_item_found
        :param start_le: if True, increase the search range to find start less than or equal by rounding down if start
            is in between keys, i.e. keys=[0, 10, 20], start=9 will include key=0
        :param stop_ge: if True, raise ValueError when there is no key greater than or equal to stop in buffer,
            if ignore_no_item_found is also True, return None instead of ValueError
        :return: list of items in range
        """
        with self._buffer.reader_lock() as reader:
            if only_new_items and self.last_key is not None:
                _next = self.next(peek=True, ignore_no_item_found=ignore_no_item_found)
                try:
                    _next_key = reader.key(_next)
                except TypeError as e:  # TypeError: 'NoneType' object is not subscriptable
                    if ignore_no_item_found:
                        return None
                    else:
                        raise e
                _start = start if start > _next_key else _next_key
            else:
                _start = start
            if start_le is True:
                with suppress(
                    ValueError
                ):  # ValueError: No item found with key at or below: _start
                    _start = reader.key(reader.find_le(_start))
            if stop_ge is True:
                try:
                    stop = reader.key(reader.find_ge(stop))
                except ValueError as e:  # ValueError: No item found with key at or above: stop
                    if ignore_no_item_found:
                        return None
                    else:
                        raise e

            items = reader.range(_start, stop, step)

        if not peek:
            try:
                self.last_item = items[-1]
            except IndexError as e:  # IndexError: list index out of range
                if ignore_no_item_found:
                    return None
                else:
                    raise e
        return items

    def tail(self, *, peek=False, ignore_no_item_found=False, only_new_items=False):
        """Finds the last item in buffer. Raise ValueError if no item found.

        :param peek: if True, last_item cursor will not be updated
        :param ignore_no_item_found: if True, return None when no next item instead of raising exception
        :param only_new_items: if True and no new items, raise ValueError or return None if ignore_no_item_found
        :return: tail item
        """
        with self._buffer.reader_lock() as reader:
            if only_new_items:
                try:
                    item = reader.find_last_gt(self.last_key)
                except ValueError as e:  # ValueError: No item found with key above: self.last_key
                    if ignore_no_item_found:
                        return None
                    else:
                        raise e
                except TypeError as e:  # TypeError: '>' not supported between instances of type(key) and 'NoneType'
                    if self.last_item is None:  # first time reading a value from buffer
                        item = reader[-1]
                    else:
                        raise e
            else:
                try:
                    item = reader[-1]
                except IndexError as e:  # IndexError: deque index out of range
                    if ignore_no_item_found:
                        return None
                    else:
                        raise e
        if not peek:
            self.last_item = item
        return item

    def head(self, *, peek=False):
        with self._buffer.reader_lock() as reader:
            item = reader[0]
        if not peek:
            self.last_item = item
        return item
