"""
A BufferReader gives data access to any number of consumers and provides methods to seek data such
as next(), range(), head(), tail().  Each BufferReader instance has it's own cursor keeping track of
what data was last seen."""

from contextlib import suppress
import threading
import time
from functools import wraps, partialmethod, partial
from typing import Optional, Union

from stream2py.source_reader import SourceReader
from stream2py.stream_buffer import StreamBuffer
from stream2py.utility.locked_sorted_deque import RWLockSortedDeque

DFLT_READ_SIZE = 1
DFLT_MAX_LEN = 10000

def defaulted_values(source_dict, defaults):
    """Returns a the values of source_dict where None values are replaced with the
    corresponding `default_dict` values.

    >>> defaults = {'a': 1, 'b': 2, 'c': 3}
    >>> tuple(defaulted_values({'a': None, 'b': 22, 'c': None}, defaults))
    (1, 22, 3)
    >>> tuple(defaulted_values({'a': False, 'b': True, 'c': None}, defaults))
    (False, True, 3)
    """
    return {
        k: v if v is not None else defaults[k] for k, v in source_dict.items()
    }.values()

# TODO: needs a check to make mk_buffer a no-op if the buffer already exists.


class StreamReader:
    """Reader that reads from a StreamBuffer. Will create a new StreamBuffer if none is provided.

    >>> from stream2py import StreamReader
    >>> from stream2py.examples.source_reader import SimpleCounterString
    >>>
    >>> source_reader = SimpleCounterString(start=0, stop=100)
    >>> stream_reader = StreamReader(source_reader, maxlen=100).mk_buffer(maxlen=100)
    >>> stream_reader.start()
    >>>
    >>> stream_reader.is_stopped
    False
    >>> stream_reader.last_item == None  # None until value is seen
    True
    >>> stream_reader.read() # get first item
    's0'
    >>> stream_reader.last_item # check last_item cursor
    's0'
    >>> # next will not update last_item cursor
    >>> stream_reader.read(peek=True), stream_reader.last_item
    ('s1', 's0')
    >>> # same as what was peeked but now cursor is updated
    >>> stream_reader.read(), stream_reader.last_item
    ('s1', 's1')
    >>> stream_reader.range(start=5, stop=10)
    ['s5', 's6', 's7', 's8', 's9', 's10']
    >>> stream_reader.last_item
    's10'
    >>> stream_reader.range(start=5, stop=10, step=3), stream_reader.last_item
    (['s5', 's8'], 's8')
    >>> stream_reader.range(start=10, stop=15, peek=True)
    ['s10', 's11', 's12', 's13', 's14', 's15']
    >>> stream_reader.last_item # unchanged with peek
    's8'
    >>> stream_reader.last_key # key of last_item
    8
    >>> # only 9 is greater than last item key
    >>> stream_reader.range(start=0, stop=9, only_new_items=True)
    ['s9']
    >>> stream_reader.head(), stream_reader.last_item, stream_reader.last_key
    ('s0', 's0', 0)
    >>> stream_reader.tail(), stream_reader.last_item, stream_reader.last_key
    ('s99', 's99', 99)
    >>>
    >>> stream_reader.stop()
    >>>
    >>> stream_reader.is_stopped
    True
    """

    read = None  # will be set by init

    def __init__(
        self,
        source,
        buffer=None,
        **source_kwargs,
    ):
        """

        The `read_size`, `peek`, `strict_n` and `ignore_no_item_found` parameters
        are used as defaults of the
        `read` method. More importanty -- since the default read is used by
        `__next__` and therefore by `__iter__`, the `read_size` and `peek` these
        parameters define the behavior of

        :param source: SourceReader,  a subclass of SourceReader, or an instance of SourceReader.
        """
        if not isinstance(source, SourceReader):
            source = source(**source_kwargs)
        self._source = source
        if not isinstance(buffer, StreamBuffer):
            buffer = StreamBuffer(source, maxlen=DFLT_MAX_LEN)
        self.stream_buffer = buffer
        self._last_item = None
        self._last_key = None
        self._sleep_time_on_iter_none_s = 0.1
        # _read_kwargs will be used as the defaults of the read method as well as
        # the kwargs of the __next__ method (with ignore_no_item_found=True forced)
        self._read_kwargs = dict(
            n=DFLT_READ_SIZE,
            ignore_no_item_found=False,
            strict_n=False,
        )
        # The _read_kwargs_for_iter should be the same as the _read_kwargs, but with
        # forced ignore_no_item_found=True so that __iter__ always returns a value, and
        # doesn't throw an error (because iter is blocking)
        self._read_kwargs_for_next = dict(self._read_kwargs, ignore_no_item_found=True)

    def __iter__(self):
        while True:
            _next = next(self)
            if _next is not None:
                yield _next
            elif self.is_stopped:
                return None
            else:
                time.sleep(self._sleep_time_on_iter_none_s)

    def __next__(self):
        # Call read with the args fixed by init
        return self.read(**self._read_kwargs_for_next)

    def mk_buffer(
        self,
        *,
        maxlen: Optional[int] = None,
        sleep_time_on_read_none_s: Optional[Union[int, float]] = None,
        auto_drop=True,
    ):
        """Sets custom buffer parameters."""
        self._buffer_kwargs = dict(
            maxlen=maxlen,
            sleep_time_on_read_none_s=sleep_time_on_read_none_s,
            auto_drop=auto_drop,
        )
        return self

    def mk_reader(self, read_size=1, strict_n=False, ignore_no_item_found=False):
        """Sets a custom read configuration for the reader.
        :param read_size: number of items to return by default when reading.
            Is also used as the "chunk size" when iterating.
        :param ignore_no_item_found: if True, by default return None when no next item
            instead of raising exception during a read
        :param strict_n: if True, by default a ValueError witll be raised if the
            exact number of requested items are not available when reading.
        """

        self.read_size = read_size  # read_size used by __next__
        self.ignore_no_item_found = ignore_no_item_found
        self.strict_n = strict_n
        # _read_kwargs will be used as the defaults of the read method as well as
        # the kwargs of the __next__ method (with ignore_no_item_found=True forced)
        self._read_kwargs = dict(
            n=self.read_size,
            ignore_no_item_found=self.ignore_no_item_found,
            strict_n=self.strict_n,
        )
        return self

    def set_sleep_time_on_iter_none(self, sleep_time_s: Union[int, float] = 0.1):
        """Set the sleep time of the iter yield loop when next data item is not yet available.

        :param sleep_time_s: seconds to sleep
        """
        self._sleep_time_on_iter_none_s = sleep_time_s

    def is_same_buffer(self, other_buffer_reader):
        """Check if reader is looking at the same buffer"""
        return (
            self._buffer == other_buffer_reader._buffer
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
        return self._source.info

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

    def range(
        self,
        start,
        stop,
        step=None,
        *,
        peek=False,
        ignore_no_item_found=None,
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
        :param ignore_no_item_found: if True, return None when no next item
            instead of raising exception.
        :param only_new_items: if True and no new items, raise ValueError
            or return None if ignore_no_item_found
        :param start_le: if True, increase the search range to find start less than or equal by
            rounding down if start is in between keys,
            i.e. keys=[0, 10, 20], start=9 will include key=0
        :param stop_ge: if True, raise ValueError when there is no key greater than or equal to
            stop in buffer, if ignore_no_item_found is also True, return None instead of ValueError
        :return: list of items in range
        """
        if ignore_no_item_found is None:
            ignore_no_item_found = self._read_kwargs.get('ignore_no_item_found', False)
        with self._buffer.reader_lock() as reader:
            if only_new_items and self.last_key is not None:
                _next = self.read(
                    n=1, peek=True, ignore_no_item_found=ignore_no_item_found
                )
                try:
                    _next_key = reader.key(_next)
                except TypeError as e:  # TypeError: 'NoneType' object is not subscriptable
                    if ignore_no_item_found:
                        return None
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
                    raise e

            items = reader.range(_start, stop, step)

        if not peek:
            try:
                self.last_item = items[-1]
            except IndexError as e:  # IndexError: list index out of range
                if ignore_no_item_found:
                    return None
                raise e
        return items

    def tail(self, *, peek=False, ignore_no_item_found=False, only_new_items=False):
        """Finds the last item in buffer. Raise ValueError if no item found.

        :param peek: if True, last_item cursor will not be updated
        :param ignore_no_item_found: if True, return None when no next item
            instead of raising exception
        :param only_new_items: if True and no new items, raise ValueError
            or return None if ignore_no_item_found
        :return: tail item
        """
        with self._buffer.reader_lock() as reader:
            if only_new_items:
                try:
                    item = reader.find_last_gt(self.last_key)
                except ValueError as e:  # ValueError: No item found with key above: self.last_key
                    if ignore_no_item_found:
                        return None
                    raise e
                except TypeError as e:
                    # TypeError: '>' not supported between instances of type(key) and 'NoneType'
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

    def read(self, n=None, *, peek=None, ignore_no_item_found=None, strict_n=None):
        """Finds an item with a key greater than the last returned item.
        Raise ValueError if no item found with key above last item.

        Note: Arguments whose values are not specified will be replaced with
        self.

        :param n: number of items to return
        :param peek: if True, last_item cursor will not be updated
        :param ignore_no_item_found: if True, return None when no next item
            instead of raising exception
        :param strict_n: if True, raise ValueError if n items are not available
        :return: next item or list of next items if n > 1
        """
        n, ignore_no_item_found, strict_n = defaulted_values(
            dict(
                n=n,
                ignore_no_item_found=ignore_no_item_found,
                strict_n=strict_n,
            ),
            defaults=self._read_kwargs,
        )

        with self._buffer.reader_lock() as reader:
            try:
                next_item = reader.find_gt(self.last_key)
            except ValueError as e:  # ValueError: No item found with key above:
                # self.last_key
                if ignore_no_item_found:
                    return None
                raise e
            except TypeError as e:
                # TypeError: '<' not supported between instances of 'NoneType' and type(key)
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
            if not peek:
                self.last_item = next_item
            return next_item

    def fork(self, **reader_kwargs):
        """Creates a new reader for the same buffer.
        """
        if not self._buffer:
            raise ValueError('Must start reader before forking.')
        new_reader = StreamReader(self._source, self.stream_buffer).mk_reader(**reader_kwargs)
        new_reader._buffer = self._buffer
        new_reader._stop_event = self._stop_event
        return new_reader

    def start(self):
        self.stream_buffer.start()
        self.stream_buffer.attach_reader(self)

    def stop(self):
        self.stream_buffer.stop()

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
